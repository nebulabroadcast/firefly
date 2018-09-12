#!/usr/bin/env python3

import sys
import time
import functools

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui  import *

from .mpv import MPV
from nxtools import *


class TimecodeWindow(QLineEdit):
    def __init__(self, parent=None):
        super(TimecodeWindow, self).__init__(parent)
        self.setText("00:00:00:00")
        self.setInputMask("99:99:99:99")

        fm = self.fontMetrics()
        w = fm.boundingRect(self.text()).width() + 16
        self.setMinimumWidth(w)
        self.setMaximumWidth(w)


class ToolBarStretcher(QWidget):
    def __init__(self, parent):
        super(ToolBarStretcher, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


class RegionBar(QWidget):
    def __init__(self,parent):
        super(RegionBar, self).__init__(parent)
        self.marks_color = QColor("#009fbc")
        self.bad_marks_color = QColor("#9f0000")
        self.setFixedHeight(6)
        self.show()

    def paintEvent(self, event=False):
        qp = QPainter()
        qp.begin(self)
        self.drawRegion(qp)
        qp.end()

    @property
    def duration(self):
        return self.parent().duration

    @property
    def mark_in(self):
        return self.parent().mark_in

    @property
    def mark_out(self):
        return self.parent().mark_out or self.parent().duration

    def drawRegion(self, qp):
        if not self.duration:
            return
        w = self.width()
        h = self.height()
        x1 = (float(w) / self.duration) * (self.mark_in)
        x2 = (float(w) / self.duration) * (self.mark_out - self.mark_in)
        qp.setPen(Qt.NoPen)
        if self.mark_in and self.mark_out and self.mark_in > self.mark_out:
            qp.setBrush(self.bad_marks_color)
        else:
            qp.setBrush(self.marks_color)
        qp.drawRect(x1, 1, x2, h-4)


def get_navbar(wnd):
    toolbar = QToolBar(wnd)

    #
    # Invisible actions
    #

    wnd.action_clear_marks = QAction(wnd)
    wnd.action_clear_marks.setShortcuts(['g'])
    wnd.action_clear_marks.setStatusTip('Clear both marks')
    wnd.action_clear_marks.triggered.connect(wnd.on_clear_marks)
    toolbar.addAction(wnd.action_clear_marks)


    #
    # Buttons
    #

    wnd.action_clear_in = QAction(QIcon(wnd.pixlib["clear-in"]), "Clear In", wnd)
    wnd.action_clear_in.setShortcut('d')
    wnd.action_clear_in.setStatusTip('Clear in')
    wnd.action_clear_in.triggered.connect(wnd.on_clear_in)
    toolbar.addAction(wnd.action_clear_in)

    wnd.action_mark_in = QAction(QIcon(wnd.pixlib["mark-in"]), "Mark in", wnd)
    wnd.action_mark_in.setShortcuts(['e', 'i'])
    wnd.action_mark_in.setStatusTip('Mark in')
    wnd.action_mark_in.triggered.connect(wnd.on_mark_in)
    toolbar.addAction(wnd.action_mark_in)

    wnd.action_goto_in = QAction(QIcon(wnd.pixlib["goto-in"]), "Go to in", wnd)
    wnd.action_goto_in.setShortcut('q')
    wnd.action_mark_in.setStatusTip('Go to selection start')
    wnd.action_goto_in.triggered.connect(wnd.on_go_in)
    toolbar.addAction(wnd.action_goto_in)

    toolbar.addWidget(ToolBarStretcher(wnd))

    wnd.action_go_start = QAction(QIcon(wnd.pixlib["fast-backward"]), 'Go to start', wnd)
    wnd.action_go_start.setShortcuts(['a', 'home'])
    wnd.action_go_start.triggered.connect(wnd.on_go_start)
    wnd.addAction(wnd.action_go_start)
    toolbar.addAction(wnd.action_go_start)

    wnd.action_frame_prev5 = QAction(QIcon(wnd.pixlib["previous-more"]), 'Previous 5 frames', wnd)
    wnd.action_frame_prev5.setShortcuts(['1', 'j'])
    wnd.action_frame_prev5.triggered.connect(wnd.on_5_prev)
    wnd.addAction(wnd.action_frame_prev5)
    toolbar.addAction(wnd.action_frame_prev5)

    wnd.action_frame_prev = QAction(QIcon(wnd.pixlib["previous"]), "Previous frame", wnd)
    wnd.action_frame_prev.setShortcuts(['3', 'Left'])
    wnd.action_frame_prev.setStatusTip('Go to previous frame')
    wnd.action_frame_prev.triggered.connect(wnd.on_frame_prev)
    toolbar.addAction(wnd.action_frame_prev)

    wnd.action_play = QAction(QIcon(wnd.pixlib["play"]), "Play", wnd)
    wnd.action_play.setShortcuts(['Space', 'k'])
    wnd.action_play.setStatusTip('Play/Pause')
    wnd.action_play.triggered.connect(wnd.on_pause)
    toolbar.addAction(wnd.action_play)

    wnd.action_frame_next = QAction(QIcon(wnd.pixlib["next"]), "Next frame", wnd)
    wnd.action_frame_next.setShortcuts(['4', 'Right'])
    wnd.action_frame_next.setStatusTip('Go to next frame')
    wnd.action_frame_next.triggered.connect(wnd.on_frame_next)
    toolbar.addAction(wnd.action_frame_next)

    wnd.action_frame_next5 = QAction(QIcon(wnd.pixlib["next-more"]), 'Next 5 frames', wnd)
    wnd.action_frame_next5.setShortcuts(['2', 'l'])
    wnd.action_frame_next5.triggered.connect(wnd.on_5_next)
    wnd.addAction(wnd.action_frame_next5)
    toolbar.addAction(wnd.action_frame_next5)

    wnd.action_go_end = QAction(QIcon(wnd.pixlib["fast-forward"]), 'Go to end', wnd)
    wnd.action_go_end.setShortcuts(['s', 'end'])
    wnd.action_go_end.triggered.connect(wnd.on_go_end)
    wnd.addAction(wnd.action_go_end)
    toolbar.addAction(wnd.action_go_end)

    toolbar.addWidget(ToolBarStretcher(wnd))

    wnd.action_goto_out = QAction(QIcon(wnd.pixlib["goto-out"]), "Go to out", wnd)
    wnd.action_goto_out.setShortcut('w')
    wnd.action_goto_out.setStatusTip('Go to selection end')
    wnd.action_goto_out.triggered.connect(wnd.on_go_out)
    toolbar.addAction(wnd.action_goto_out)

    wnd.action_mark_out = QAction(QIcon(wnd.pixlib["mark-out"]), "Mark out", wnd)
    wnd.action_mark_out.setShortcuts(['r', 'o'])
    wnd.action_mark_out.setStatusTip('Mark out')
    wnd.action_mark_out.triggered.connect(wnd.on_mark_out)
    toolbar.addAction(wnd.action_mark_out)

    wnd.action_clear_out = QAction(QIcon(wnd.pixlib["clear-out"]), "Clear out",wnd)
    wnd.action_clear_out.setShortcut('f')
    wnd.action_clear_out.setStatusTip('Clear out')
    wnd.action_clear_out.triggered.connect(wnd.on_clear_out)
    toolbar.addAction(wnd.action_clear_out)

    return toolbar







class VideoPlayer(QWidget):
    def __init__(self, parent=None, pixlib=None):
        super(VideoPlayer, self).__init__(parent)

        self.pixlib = pixlib

        self.video_window = QWidget(self)
        self.video_window.setStyleSheet("background-color: #161616;")
        self.player = MPV(
                    keep_open=True,
                    wid=str(int(self.video_window.winId()))
                )

        self.position = 0
        self.duration = 0
        self.mark_in  = 0
        self.mark_out = 0
        self.fps = 25.0

        self.prev_position = 0
        self.prev_duration = 0
        self.prev_mark_in  = 0
        self.prev_mark_out = 0

        @self.player.property_observer('time-pos')
        def time_observer(_name, value):
            self.on_time_change(value)

        @self.player.property_observer('duration')
        def duration_observer(_name, value):
            self.on_duration_change(value)

        #
        # Displays
        #

        self.mark_in_display = TimecodeWindow(self)
        self.mark_in_display.setToolTip("Selection start")

        self.mark_out_display = TimecodeWindow(self)
        self.mark_out_display.setToolTip("Selection end")

        self.io_display = TimecodeWindow(self)
        self.io_display.setToolTip("Selection duration")
        self.io_display.setReadOnly(True)

        self.position_display = TimecodeWindow(self)
        self.position_display.setToolTip("Clip position")

        self.duration_display = TimecodeWindow(self)
        self.duration_display.setToolTip("Clip duration")
        self.duration_display.setReadOnly(True)

        #
        # Controls
        #

        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 0)
        self.timeline.sliderMoved.connect(self.on_timeline_seek)
        self.region_bar = RegionBar(self)
        self.navbar = get_navbar(self)

        #
        # Layout
        #

        bottom_bar = QHBoxLayout()
        top_bar = QHBoxLayout()

        top_bar.addWidget(self.mark_in_display, 0)
        top_bar.addStretch(1)
        top_bar.addWidget(self.io_display, 0)
        top_bar.addStretch(1)
        top_bar.addWidget(self.mark_out_display, 0)

        bottom_bar.addWidget(self.position_display, 0)
        bottom_bar.addWidget(self.navbar, 1)
        bottom_bar.addWidget(self.duration_display, 0)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.video_window)
        layout.addWidget(self.region_bar)
        layout.addWidget(self.timeline)
        layout.addLayout(bottom_bar)

        self.setLayout(layout)
        self.navbar.setFocus(True)

        # Displays updater

        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.on_display_timer)
        self.display_timer.start(40)


    @property
    def frame_dur(self):
        return 1 / self.fps

    def load(self, path, mark_in=0, mark_out=0):
        self.player["pause"] = True
        self.player.play(path)
        self.prev_mark_in  = 0
        self.prev_mark_out = 0
        self.mark_in = mark_in
        self.mark_out = mark_out
        self.update_marks()

    def on_time_change(self, value):
        self.position = value

    def on_duration_change(self, value):
        if value:
            self.duration = value
        else:
            self.duration = 0
        self.region_bar.update()

    def on_timeline_seek(self):
        self.player["pause"] = True
        self.player.seek(self.timeline.value() / 100.0, "absolute", "exact")

    def on_frame_next(self):
        self.player.frame_step()

    def on_frame_prev(self):
        self.player.frame_back_step()

    def on_5_next(self):
        self.player.seek(5*self.frame_dur, "relative", "exact")

    def on_5_prev(self):
        self.player.seek(-5*self.frame_dur, "relative", "exact")

    def on_go_start(self):
        self.player.seek(0, "absolute", "exact")

    def on_go_end(self):
        self.player.seek(self.duration, "absolute", "exact")

    def on_go_in(self):
        self.seek(self.mark_in)

    def on_go_out(self):
        self.seek(self.mark_out or self.duration)

    def on_mark_in(self):
        self.mark_in = self.position
        self.region_bar.update()

    def on_mark_out(self):
        self.mark_out = self.position
        self.region_bar.update()

    def on_clear_in(self):
        self.mark_in = 0
        self.region_bar.update()

    def on_clear_out(self):
        self.mark_out = 0
        self.region_bar.update()

    def on_clear_marks(self):
        self.mark_out = self.mark_in = 0
        self.region_bar.update()

    def seek(self, position):
        self.player.seek(position, "absolute", "exact")

    def on_pause(self):
        self.player["pause"] = not self.player["pause"]

    def update_marks(self):
        i = self.mark_in
        o = self.mark_out or self.duration
        self.mark_in_display.setText(s2tc(i))
        self.mark_out_display.setText(s2tc(o))
        io = o - i + self.frame_dur
        if io > 0:
            self.io_display.setText(s2tc(io))
        else:
            self.io_display.setText("<font color='red'>00:00:00:00</font>")
        self.prev_mark_in = self.mark_in
        self.prev_mark_out = self.mark_out

    def on_display_timer(self):
        if self.position != self.prev_position and self.position is not None:
            self.position_display.setText(s2tc(self.position))
            self.timeline.setValue(int(self.position*100))
            self.prev_position = self.position

        if self.duration != self.prev_duration and self.position is not None:
            self.duration_display.setText(s2tc(self.duration))
            self.timeline.setMaximum(int(self.duration*100))
            self.prev_duration = self.duration

        if self.mark_in != self.prev_mark_in or self.mark_out != self.prev_mark_out:
            self.update_marks()



if __name__ == "__main__":
    path = "https://sport5.nebulabroadcast.com/proxy/0001/1000.mp4"

    class Test(QMainWindow):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.player = VideoPlayer(self)
            self.setCentralWidget(self.player)
            self.player.load(path)

    app = QApplication(sys.argv)

    import locale
    locale.setlocale(locale.LC_NUMERIC, 'C')
    win = Test()
    win.show()
    sys.exit(app.exec_())
