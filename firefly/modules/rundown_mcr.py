import math

from firefly import *

PROGRESS_BAR_RESOLUTION = 2000

class MCRButton(QPushButton):
    def __init__(self, title, parent=None, on_click=False):
        super(MCRButton, self).__init__(parent)
        self.setText(title)
        if title == "Freeze":
            bg_col = "#941010"
            self.setToolTip("Pause/unpause current clip")
        elif title == "Take":
            bg_col = "#109410"
            self.setToolTip("Start cued clip")
        else:
            bg_col = "#565656"
        self.setStyleSheet("""
            MCRButton {{
                font-size:14px;
                color: #eeeeee;
                width: 80px;
                height:30px;
                border: 2px solid {};
                text-transform: uppercase;
            }}

            MCRButton:pressed {{
                border: 2px solid #00a5c3;
            }}""".format(bg_col))

        if on_click:
            self.clicked.connect(on_click)


class MCRLabel(QLabel):
    def __init__(self, head, default, parent=None, tcolor="#eeeeee"):
        super(MCRLabel,self).__init__(parent)
        self.head = head
        self.setStyleSheet("""
                background-color: #161616;
                padding:5px;
                margin:3px;
                font:16px;
                font-weight: bold;
                color : {};
            """.format(tcolor))
        self.set_text(default)

    def set_text(self,text):
        self.setText(self.head + ": " + text)


class MCR(QWidget):
    def __init__(self, parent):
        super(MCR, self).__init__(parent)

        self.pos = 0
        self.dur = 0
        self.current  = "(loading)"
        self.cued     = "(loading)"
        self.request_time = 0
        self.paused = False
        self.stopped = True
        self.cueing = False
        self.local_request_time = time.time()
        self.updating = False
        self.request_display_resize = False

        self.fps = 25.0

        self.parent().setWindowTitle("On air ctrl")

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(PROGRESS_BAR_RESOLUTION)

        self.btn_take    = MCRButton("Take",   self, self.on_take)
        self.btn_freeze  = MCRButton("Freeze", self, self.on_freeze)
        self.btn_retake  = MCRButton("Retake", self, self.on_retake)
        self.btn_abort   = MCRButton("Abort",  self, self.on_abort)

        can_mcr = True #TODO: ACL
        self.btn_take.setEnabled(can_mcr)
        self.btn_freeze.setEnabled(can_mcr)
        self.btn_retake.setEnabled(can_mcr)
        self.btn_abort.setEnabled(can_mcr)

        btns_layout = QHBoxLayout()

        btns_layout.addStretch(1)
        btns_layout.addWidget(self.btn_take ,0)
        btns_layout.addWidget(self.btn_freeze ,0)
        btns_layout.addWidget(self.btn_retake,0)
        btns_layout.addWidget(self.btn_abort,0)
        btns_layout.addStretch(1)

        self.display_clock   = MCRLabel("CLK", "--:--:--:--")
        self.display_pos     = MCRLabel("POS", "--:--:--:--")

        self.display_current = MCRLabel("CUR","(no clip)", tcolor="#cc0000")
        self.display_cued    = MCRLabel("NXT","(no clip)", tcolor="#00cc00")

        self.display_rem     = MCRLabel("REM","(unknown)")
        self.display_dur     = MCRLabel("DUR", "--:--:--:--")


        info_layout = QGridLayout()
        info_layout.setContentsMargins(0,0,0,0)
        info_layout.setSpacing(2)

        info_layout.addWidget(self.display_clock,   0, 0)
        info_layout.addWidget(self.display_pos,     1, 0)

        info_layout.addWidget(self.display_current, 0, 1)
        info_layout.addWidget(self.display_cued,    1, 1)

        info_layout.addWidget(self.display_rem,     0, 2)
        info_layout.addWidget(self.display_dur,     1, 2)

        info_layout.setColumnStretch(1,1)

        layout = QVBoxLayout()
        layout.addLayout(info_layout,0)
        layout.addWidget(self.progress_bar,0)
        layout.addLayout(btns_layout,0)
        self.setLayout(layout)

        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(40)

    @property
    def id_channel(self):
        return self.parent().id_channel

    def on_take(self):
        api.playout(timeout=1, action="take", id_channel=self.id_channel)

    def on_freeze(self):
        self.paused = not self.paused
        api.playout(timeout=1, action="freeze", id_channel=self.id_channel)

    def on_retake(self):
        api.playout(timeout=1, action="retake", id_channel=self.id_channel)

    def on_abort(self):
        api.playout(timeout=1, action="abort", id_channel=self.id_channel)

    def seismic_handler(self, data):
        status = data.data
        self.pos = status["position"] + (1/self.fps)
        self.request_time = status["request_time"]
        self.paused = status["paused"]
        self.stopped = status["stopped"]
        self.local_request_time = time.time()

        if status["fps"] != self.fps:
            self.fps = status["fps"]

        if self.dur != status["duration"]:
            self.dur = status["duration"]
            self.display_dur.set_text(f2tc(self.dur, self.fps))
            self.request_display_resize = False

        if self.current != status["current_title"]:
            self.current = status["current_title"]
            self.display_current.set_text(self.current)
            self.request_display_resize = False

        cueing = status.get("cueing", False)
        if self.cued != status["cued_title"] or self.cueing != cueing:
            self.cued = status["cued_title"]
            if cueing:
                self.display_cued.set_text("<font color='yellow'>{}</font>".format(self.cued))
            else:
                self.display_cued.set_text(self.cued)
            self.cueing = cueing
            self.request_display_resize = False

    def show(self, *args, **kwargs):
        super(MCR, self).show(*args, **kwargs)
        self.request_display_resize = True


    def update_display(self):
        now = time.time()
        adv = now - self.local_request_time

        rtime = self.request_time+adv
        rpos = self.pos

        if not (self.paused or self.stopped):
            rpos += adv * self.fps

        clock = time.strftime("%H:%M:%S:{:02d}", time.localtime(rtime)).format(int(25*(rtime-math.floor(rtime))))
        self.display_clock.set_text(clock)
        self.display_pos.set_text(f2tc(min(self.dur, rpos), self.fps))

        rem = self.dur - rpos
        t = f2tc(max(0, rem), self.fps)
        if rem < 250:
            self.display_rem.set_text("<font color='red'>{}</font>".format(t))
        else:
            self.display_rem.set_text(t)

        if self.pos == self.dur == self.progress_bar.value() == 0:
            self.progress_bar.setValue(0)

        try:
            ppos = int((rpos/self.dur) * PROGRESS_BAR_RESOLUTION)
        except ZeroDivisionError:
            return
        else:
            oldval = self.progress_bar.value()
            if ppos > oldval or abs(oldval-ppos) > (PROGRESS_BAR_RESOLUTION/self.dur)*self.fps:
                self.progress_bar.setValue(ppos)

        if self.request_display_resize:
            QApplication.processEvents()
            self.display_clock.setFixedSize(self.display_clock.size())
            self.display_pos.setFixedSize(self.display_clock.size())
            self.display_rem.setFixedSize(self.display_clock.size())
            self.display_dur.setFixedSize(self.display_clock.size())
            self.request_display_resize = False
