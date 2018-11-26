import datetime

from firefly import *



ITEM_BUTTONS = [
    {
        "icon"      : "placeholder",
        "title"     : "Placeholder",
        "duration"  : 3600,
        "item_role" : "placeholder",
        "tooltip"   : "Drag this to rundown to create placeholder",
    },

    {
        "icon"      : "live",
        "title"     : "Live",
        "duration"  : 3600,
        "item_role" : "live",
        "tooltip"   : "Drag this to rundown to create live item",
    },

    {
        "icon"      : "lead-in",
        "title"     : "Lead-in",
        "item_role" : "lead_in",
        "tooltip"   : "Drag this to rundown to create Lead-in",
    },

    {
        "icon"      : "lead-out",
        "title"     : "Lead-out",
        "item_role" : "lead_out",
        "tooltip"   : "Drag this to rundown to create Lead-out",
    }
]


def get_date():
    class CalendarDialog(QDialog):
        def __init__(self):
            super(CalendarDialog, self).__init__()
            self.setWindowTitle('Calendar')
            self.date = False, False, False
            self.setModal(True)
            self.calendar = QCalendarWidget(self)
            self.calendar.setGridVisible(True)
            self.calendar.setFirstDayOfWeek(1)
            self.calendar.activated[QDate].connect(self.setDate)
            layout = QVBoxLayout()
            layout.addWidget(self.calendar)
            self.setLayout(layout)
            self.show()

        def setDate(self, date):
            self.date = (date.year(), date.month(), date.day())
            self.close()

    cal = CalendarDialog()
    cal.exec_()
    return cal.date


def day_start(ts, start):
    hh, mm = start
    r = ts - (hh*3600 + mm*60)
    dt = datetime.datetime.fromtimestamp(r).replace(
        hour = hh,
        minute = mm,
        second = 0
        )
    return time.mktime(dt.timetuple())


class ItemButton(QToolButton):
    def __init__(self, parent, config):
        super(ItemButton, self).__init__()
        self.button_config = config
        self.pressed.connect(self.startDrag)
        self.setIcon(QIcon(pix_lib[self.button_config["icon"]]))
        self.setToolTip(self.button_config["tooltip"])

    def startDrag(self):
        item_data = {}
        for key in self.button_config:
            if key not in ["tooltip", "icon"]:
                item_data[key] = self.button_config[key]
        drag = QDrag(self);
        mimeData = QMimeData()
        mimeData.setData(
           "application/nx.item",
           encode_if_py3(json.dumps([item_data]))
           )
        drag.setMimeData(mimeData)
        if drag.exec_(Qt.CopyAction):
            pass # nejak to rozumne ukonc


def rundown_toolbar(wnd):
    action_find = QAction('Search rundown', wnd)
    action_find.setShortcut('Ctrl+F')
    action_find.triggered.connect(wnd.find)
    wnd.addAction(action_find)

    action_find_next = QAction('Search rundown', wnd)
    action_find_next.setShortcut('F3')
    action_find_next.triggered.connect(wnd.find_next)
    wnd.addAction(action_find_next)

    toolbar = QToolBar(wnd)

    action_day_prev = QAction(QIcon(pix_lib["previous"]), '&Previous day', wnd)
    action_day_prev.setShortcut('Alt+Left')
    action_day_prev.setStatusTip('Go to previous day')
    action_day_prev.triggered.connect(wnd.go_day_prev)
    toolbar.addAction(action_day_prev)

    action_now = QAction(QIcon(pix_lib["now"]), '&Now', wnd)
    action_now.setStatusTip('Go to now')
    action_now.triggered.connect(wnd.go_now)
    toolbar.addAction(action_now)

    action_calendar = QAction(QIcon(pix_lib["calendar"]), '&Calendar', wnd)
    action_calendar.setShortcut('Ctrl+D')
    action_calendar.setStatusTip('Open calendar')
    action_calendar.triggered.connect(wnd.show_calendar)
    toolbar.addAction(action_calendar)

    action_refresh = QAction(QIcon(pix_lib["refresh"]), '&Refresh', wnd)
    action_refresh.setStatusTip('Refresh rundown')
    action_refresh.triggered.connect(wnd.load)
    toolbar.addAction(action_refresh)

    action_day_next = QAction(QIcon(pix_lib["next"]), '&Next day', wnd)
    action_day_next.setShortcut('Alt+Right')
    action_day_next.setStatusTip('Go to next day')
    action_day_next.triggered.connect(wnd.go_day_next)
    toolbar.addAction(action_day_next)

    if user.has_right("rundown_edit", anyval=True):

        toolbar.addSeparator()

        for btn_config in ITEM_BUTTONS:
            toolbar.addWidget(ItemButton(wnd, btn_config))

        toolbar.addSeparator()

        action_toggle_mcr = QAction(QIcon(pix_lib["mcr"]), '&Playout controls', wnd)
        action_toggle_mcr.setStatusTip('Toggle playout controls')
        action_toggle_mcr.triggered.connect(wnd.toggle_mcr)
        toolbar.addAction(action_toggle_mcr)

        action_toggle_plugins = QAction(QIcon(pix_lib["plugins"]), '&Plugins controls', wnd)
        action_toggle_plugins.setShortcut('F4')
        action_toggle_plugins.setStatusTip('Toggle plugins controls')
        action_toggle_plugins.triggered.connect(wnd.toggle_plugins)
        toolbar.addAction(action_toggle_plugins)

    toolbar.addWidget(ToolBarStretcher(wnd))

    wnd.channel_display = ChannelDisplay()
    toolbar.addWidget(wnd.channel_display)

    return toolbar



