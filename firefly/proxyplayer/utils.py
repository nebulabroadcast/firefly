from nxtools import s2tc
from firefly.qt import (
    QLineEdit,
    QSizePolicy,
    QWidget,
    QColor,
    QPainter,
    Qt,
    QToolBar,
    QAction,
    QIcon,
)


class TimecodeWindow(QLineEdit):
    def __init__(self, parent=None):
        super(TimecodeWindow, self).__init__(parent)
        self.setText("00:00:00:00")
        self.setInputMask("99:99:99:99")

        fm = self.fontMetrics()
        w = fm.boundingRect(self.text()).width() + 16
        self.setMinimumWidth(w)
        self.setMaximumWidth(w)

    @property
    def fps(self):
        return self.parent().fps

    def set_value(self, value):
        self.setText(s2tc(value, self.fps))
        self.setCursorPosition(0)

    def get_value(self):
        hh, mm, ss, ff = [int(i) for i in self.text().split(":")]
        return (hh * 3600) + (mm * 60) + ss + (ff / self.fps)


class ToolBarStretcher(QWidget):
    def __init__(self, parent):
        super(ToolBarStretcher, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


class RegionBar(QWidget):
    def __init__(self, parent):
        super(RegionBar, self).__init__(parent)
        self.marks_color = QColor("#009fbc")
        self.bad_marks_color = QColor("#9f0000")
        self.setFixedHeight(6)
        self.show()

    def paintEvent(self, event=False):
        qp = QPainter()
        qp.begin(self)
        self.draw_timeline(qp)
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

    def draw_timeline(self, qp):
        if not self.duration:
            return
        qp.setPen(Qt.PenStyle.NoPen)

        w = self.width()
        h = self.height()

        # in/out
        x1 = int((float(w) / self.duration) * (self.mark_in))
        x2 = int((float(w) / self.duration) * (self.mark_out - self.mark_in))
        if self.mark_in and self.mark_out and self.mark_in > self.mark_out:
            qp.setBrush(self.bad_marks_color)
        else:
            qp.setBrush(self.marks_color)
        qp.drawRect(x1, 1, x2, h - 4)

        # markers
        for marker_id in self.parent().markers:
            marker = self.parent().markers[marker_id]
            qp.setBrush(QColor(marker.get("color", "#ccaa00")))
            x = int((float(w) / self.duration) * marker["position"])
            qp.drawRect(x, 0, 2, h)


def get_navbar(wnd):
    toolbar = QToolBar(wnd)

    #
    # Invisible actions
    #

    wnd.action_clear_marks = QAction(wnd)
    wnd.action_clear_marks.setShortcuts(["g"])
    wnd.action_clear_marks.setStatusTip("Clear both marks")
    wnd.action_clear_marks.triggered.connect(wnd.on_clear_marks)
    toolbar.addAction(wnd.action_clear_marks)

    #
    # Buttons
    #

    wnd.action_clear_in = QAction(QIcon(wnd.pixlib["clear-in"]), "Clear In", wnd)
    wnd.action_clear_in.setShortcut("d")
    wnd.action_clear_in.setStatusTip("Clear in")
    wnd.action_clear_in.triggered.connect(wnd.on_clear_in)
    toolbar.addAction(wnd.action_clear_in)

    wnd.action_mark_in = QAction(QIcon(wnd.pixlib["mark-in"]), "Mark in", wnd)
    wnd.action_mark_in.setShortcuts(["e", "i"])
    wnd.action_mark_in.setStatusTip("Mark in")
    wnd.action_mark_in.triggered.connect(wnd.on_mark_in)
    toolbar.addAction(wnd.action_mark_in)

    wnd.action_goto_in = QAction(QIcon(wnd.pixlib["goto-in"]), "Go to in", wnd)
    wnd.action_goto_in.setShortcut("q")
    wnd.action_mark_in.setStatusTip("Go to selection start")
    wnd.action_goto_in.triggered.connect(wnd.on_go_in)
    toolbar.addAction(wnd.action_goto_in)

    toolbar.addWidget(ToolBarStretcher(wnd))

    wnd.action_go_start = QAction(
        QIcon(wnd.pixlib["fast-backward"]), "Go to start", wnd
    )
    wnd.action_go_start.setShortcuts(["a", "home"])
    wnd.action_go_start.triggered.connect(wnd.on_go_start)
    wnd.addAction(wnd.action_go_start)
    toolbar.addAction(wnd.action_go_start)

    wnd.action_frame_prev5 = QAction(
        QIcon(wnd.pixlib["previous-more"]), "Previous 5 frames", wnd
    )
    wnd.action_frame_prev5.setShortcuts(["1", "j"])
    wnd.action_frame_prev5.triggered.connect(wnd.on_5_prev)
    wnd.addAction(wnd.action_frame_prev5)
    toolbar.addAction(wnd.action_frame_prev5)

    wnd.action_frame_prev = QAction(
        QIcon(wnd.pixlib["previous"]), "Previous frame", wnd
    )
    wnd.action_frame_prev.setShortcuts(["3", "Left"])
    wnd.action_frame_prev.setStatusTip("Go to previous frame")
    wnd.action_frame_prev.triggered.connect(wnd.on_frame_prev)
    toolbar.addAction(wnd.action_frame_prev)

    wnd.action_play = QAction(QIcon(wnd.pixlib["play"]), "Play", wnd)
    wnd.action_play.setShortcuts(["Space", "k"])
    wnd.action_play.setStatusTip("Play/Pause")
    wnd.action_play.triggered.connect(wnd.on_pause)
    toolbar.addAction(wnd.action_play)

    wnd.action_frame_next = QAction(QIcon(wnd.pixlib["next"]), "Next frame", wnd)
    wnd.action_frame_next.setShortcuts(["4", "Right"])
    wnd.action_frame_next.setStatusTip("Go to next frame")
    wnd.action_frame_next.triggered.connect(wnd.on_frame_next)
    toolbar.addAction(wnd.action_frame_next)

    wnd.action_frame_next5 = QAction(
        QIcon(wnd.pixlib["next-more"]), "Next 5 frames", wnd
    )
    wnd.action_frame_next5.setShortcuts(["2", "l"])
    wnd.action_frame_next5.triggered.connect(wnd.on_5_next)
    wnd.addAction(wnd.action_frame_next5)
    toolbar.addAction(wnd.action_frame_next5)

    wnd.action_go_end = QAction(QIcon(wnd.pixlib["fast-forward"]), "Go to end", wnd)
    wnd.action_go_end.setShortcuts(["s", "end"])
    wnd.action_go_end.triggered.connect(wnd.on_go_end)
    wnd.addAction(wnd.action_go_end)
    toolbar.addAction(wnd.action_go_end)

    toolbar.addWidget(ToolBarStretcher(wnd))

    wnd.action_goto_out = QAction(QIcon(wnd.pixlib["goto-out"]), "Go to out", wnd)
    wnd.action_goto_out.setShortcut("w")
    wnd.action_goto_out.setStatusTip("Go to selection end")
    wnd.action_goto_out.triggered.connect(wnd.on_go_out)
    toolbar.addAction(wnd.action_goto_out)

    wnd.action_mark_out = QAction(QIcon(wnd.pixlib["mark-out"]), "Mark out", wnd)
    wnd.action_mark_out.setShortcuts(["r", "o"])
    wnd.action_mark_out.setStatusTip("Mark out")
    wnd.action_mark_out.triggered.connect(wnd.on_mark_out)
    toolbar.addAction(wnd.action_mark_out)

    wnd.action_clear_out = QAction(QIcon(wnd.pixlib["clear-out"]), "Clear out", wnd)
    wnd.action_clear_out.setShortcut("f")
    wnd.action_clear_out.setStatusTip("Clear out")
    wnd.action_clear_out.triggered.connect(wnd.on_clear_out)
    toolbar.addAction(wnd.action_clear_out)

    return toolbar
