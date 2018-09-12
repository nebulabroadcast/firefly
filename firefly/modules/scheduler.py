import datetime

from firefly import *

from .scheduler_model import *
from .scheduler_utils import dump_template

from firefly.dialogs.event import EventDialog


EMPTY_EVENT_DATA = '[{"id" : 0, "title" : "Empty event"}]'.encode("ascii")

class EmptyEventButton(QToolButton):
    def __init__(self, parent):
        super(EmptyEventButton, self).__init__()
        self.pressed.connect(self.startDrag)
        self.setIcon(QIcon(pix_lib["empty-event"]))
        self.setToolTip("Drag this to scheduler to create empty event.")

    def startDrag(self):
        drag = QDrag(self);
        mimeData = QMimeData()
        mimeData.setData(
           "application/nx.event",
           EMPTY_EVENT_DATA
           )
        drag.setMimeData(mimeData)
        if drag.exec_(Qt.CopyAction):
            pass # nejak to rozumne ukoncit


def scheduler_toolbar(wnd):
    toolbar = QToolBar(wnd)

    action_week_prev = QAction(QIcon(pix_lib["previous"]), '&Previous week', wnd)
    action_week_prev.setShortcut('Alt+Left')
    action_week_prev.setStatusTip('Go to previous week')
    action_week_prev.triggered.connect(wnd.on_week_prev)
    toolbar.addAction(action_week_prev)

    action_refresh = QAction(QIcon(pix_lib["refresh"]), '&Refresh', wnd)
    action_refresh.setStatusTip('Refresh scheduler')
    action_refresh.triggered.connect(wnd.load)
    toolbar.addAction(action_refresh)

    action_week_next = QAction(QIcon(pix_lib["next"]), '&Next week', wnd)
    action_week_next.setShortcut('Alt+Right')
    action_week_next.setStatusTip('Go to next week')
    action_week_next.triggered.connect(wnd.on_week_next)
    toolbar.addAction(action_week_next)

    toolbar.addSeparator()

    wnd.action_show_runs = QAction(QIcon(pix_lib["show-runs"]), '&Show runs', wnd)
    wnd.action_show_runs.setStatusTip('Show runs')
    wnd.action_show_runs.setCheckable(True)
    toolbar.addAction(wnd.action_show_runs)

    toolbar.addSeparator()

    toolbar.addWidget(EmptyEventButton(wnd))

    toolbar.addWidget(ToolBarStretcher(wnd))

    wnd.channel_display = ChannelDisplay()
    toolbar.addWidget(wnd.channel_display)

    return toolbar


class SchedulerModule(BaseModule):
    def __init__(self, parent):
        super(SchedulerModule, self).__init__(parent)
        toolbar = scheduler_toolbar(self)
        self.calendar = SchedulerCalendar(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(2)
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.calendar, 1)

        self.setLayout(layout)

    def export_template(self):
        data = dump_template(self.calendar)
        try:
            if not os.path.exists("templates"):
                os.makedirs("templates")
        except Exception:
            log_traceback()
        save_file_path = QFileDialog.getSaveFileName(
                    self,
                    'Save scheduler template',
                    os.path.abspath("templates"),
                    "Templates (*.xml)"
                )[0]
        if os.path.splitext(save_file_path)[1].lower() != ".xml":
            save_file_path += ".xml"
        try:
            with open(save_file_path, 'wb') as save_file:
                save_file.write(encode_if_py3(data))
        except Exception:
            log_traceback()

    def import_template(self):
        try:
            if not os.path.exists("templates"):
                os.makedirs("templates")
        except Exception:
            log_traceback()
        file_path = QFileDialog.getOpenFileName(
                self,
                "Open template",
                os.path.abspath("templates"),
                "Templates (*.xml)"
            )[0]

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            feed = decode_if_py3(open(file_path, "rb").read())
            data = xml(feed)
        except Exception:
            QApplication.restoreOverrideCursor()
            log_traceback()
            return
        ch, cm = self.calendar.day_start
        events = []
        try:
            for day_index, day in enumerate(data.findall("day")):
                day_start = self.calendar.week_start_time + (3600*24*day_index)
                for event_data in day.findall("event"):
                    hh, mm = [int(x) for x in event_data.attrib["time"].split(":")]

                    clock_offset = (hh*3600) + (mm*60) - (ch*3600) - (cm*60)
                    if (hh*3600) + (mm*60) < (ch*3600) - (cm*60):
                        clock_offset += 24*3600

                    start_time = day_start + clock_offset

                    event = Event(meta={"start" : start_time})
                    for m in event_data.findall("meta"):
                        key = m.attrib["key"]
                        value = m.text
                        if value:
                            event[key] = value
#                    event.meta["_items"]
                    events.append(event.meta)
        except Exception:
            QApplication.restoreOverrideCursor()
            log_traceback("Unable to parse template:")
            return
        if not events:
            QApplication.restoreOverrideCursor()
            return
        response = api.schedule(
                id_channel=self.id_channel,
                events=events
            )
        QApplication.restoreOverrideCursor()
        if response.is_error:
            logging.error(response.message)
        else:
            logging.info(response.message)
        self.load()

    def load(self, *args, **kwargs):
        self.calendar.load(*args, **kwargs)
        date = datetime.date.fromtimestamp(self.calendar.week_start_time)
        week_no = date.isocalendar()[1]
        header = "Week {} - {}".format(week_no, self.playout_config["title"])
        self.channel_display.setText(header)

    def on_week_prev(self):
        self.load(self.calendar.week_start_time - (3600*24*7))

    def on_week_next(self):
        self.load(self.calendar.week_start_time + (3600*24*7))

    def focus(self, objects):
        return
        #TODO
        if self.action_show_runs.isChecked():
            asset_ids = [obj.id for obj in objects if obj.object_type == "asset"]
            if not asset_ids:
                return
            res, data = query("get_runs", id_channel=self.id_channel, asset_ids=asset_ids )
            if success(res):
                self.calendar.focus_data = data["data"]
                self.calendar.update()

    def open_rundown(self, ts, event=False):
        self.main_window.main_widget.rundown.load(start_time=ts, event=event)
        self.main_window.main_widget.switch_tab(self.main_window.main_widget.rundown)

    def set_channel(self, id_channel):
        self.load()

    def seismic_handler(self, data):
       if data.method == "objects_changed" and data.data["object_type"] == "event":
            do_load = False
            for id_event in data.data["objects"]:
                if id_event in self.calendar.event_ids:
                    do_load = True
            if do_load:
                self.load()
