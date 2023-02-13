from firefly.widgets import ToolBarStretcher, ChannelDisplay
from firefly.qt import (
    Qt,
    QToolButton,
    QIcon,
    QDrag,
    QMimeData,
    QToolBar,
    QAction,
    pixlib
)


EMPTY_EVENT_DATA = '[{"id" : 0, "title" : "Empty event"}]'.encode("ascii")


class EmptyEventButton(QToolButton):
    def __init__(self, parent):
        super(EmptyEventButton, self).__init__()
        self.pressed.connect(self.startDrag)
        self.setIcon(QIcon(pixlib["empty-event"]))
        self.setToolTip("Drag this to scheduler to create empty event.")

    def startDrag(self):
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setData("application/nx.event", EMPTY_EVENT_DATA)
        drag.setMimeData(mimeData)
        if drag.exec(Qt.DropAction.CopyAction):
            pass  # nejak to rozumne ukoncit


def scheduler_toolbar(wnd):
    toolbar = QToolBar(wnd)

    action_week_prev = QAction(QIcon(pixlib["previous"]), "&Previous week", wnd)
    action_week_prev.setShortcut("Alt+Left")
    action_week_prev.setStatusTip("Go to previous week")
    action_week_prev.triggered.connect(wnd.on_week_prev)
    toolbar.addAction(action_week_prev)

    action_refresh = QAction(QIcon(pixlib["refresh"]), "&Refresh", wnd)
    action_refresh.setStatusTip("Refresh scheduler")
    action_refresh.triggered.connect(wnd.load)
    toolbar.addAction(action_refresh)

    action_week_next = QAction(QIcon(pixlib["next"]), "&Next week", wnd)
    action_week_next.setShortcut("Alt+Right")
    action_week_next.setStatusTip("Go to next week")
    action_week_next.triggered.connect(wnd.on_week_next)
    toolbar.addAction(action_week_next)

    # TODO
    #    toolbar.addSeparator()
    #
    #    wnd.action_show_runs = QAction(QIcon(pixlib["show-runs"]), '&Show runs', wnd)
    #    wnd.action_show_runs.setStatusTip('Show runs')
    #    wnd.action_show_runs.setCheckable(True)
    #    toolbar.addAction(wnd.action_show_runs)

    toolbar.addSeparator()
    toolbar.addWidget(EmptyEventButton(wnd))
    toolbar.addWidget(ToolBarStretcher(wnd))
    wnd.channel_display = ChannelDisplay()
    toolbar.addWidget(wnd.channel_display)

    return toolbar
