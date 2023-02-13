from firefly.base_module import BaseModule
from firefly.helpers.scheduling import get_this_monday, date_offset
from firefly.qt import QVBoxLayout

from nxtools import logging

from .toolbar import scheduler_toolbar
from .calendar import SchedulerCalendar


class SchedulerModule(BaseModule):
    def __init__(self, parent):
        super(SchedulerModule, self).__init__(parent)
        toolbar = scheduler_toolbar(self)
        self.date, self.week_number = get_this_monday()
        self.calendar = SchedulerCalendar(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.calendar, 1)

        self.setLayout(layout)

    def load(self):
        self.calendar.load()
        header = (
            f"Week from {self.date} ({self.week_number})"
            f" - {self.playout_config.name}"
        )
        self.channel_display.setText(header)

    def on_week_prev(self):
        self.date, self.week_number = date_offset(self.date, -7)
        self.load()

    def on_week_next(self):
        self.date, self.week_number = date_offset(self.date, 7)
        self.load()

    def focus(self, objects):
        return
        # TODO
        if self.action_show_runs.isChecked():
            pass
            # asset_ids = [obj.id for obj in objects if obj.object_type == "asset"]
            # if not asset_ids:
            #    return
            # res, data = query(
            #     "get_runs", id_channel=self.id_channel, asset_ids=asset_ids
            # )
            # if success(res):
            #    self.calendar.focus_data = data["data"]
            #     self.calendar.update()

    def open_rundown(self, ts, event=False):
        self.main_window.main_widget.rundown.load(start_time=ts, event=event)
        self.main_window.main_widget.switch_tab(
            self.main_window.main_widget.rundown, perform_on_switch_tab=False
        )

    def on_channel_changed(self):
        logging.debug(f"[SCHEDULER] setting channel to {self.id_channel}")
        self.load()

    def refresh_events(self, events):
        for id_event in events:
            if id_event in self.calendar.event_ids:
                logging.debug(
                    f"[SCHEDULER] Event id {id_event} has been changed."
                    "Reloading calendar"
                )
                self.load()
                break

    def seismic_handler(self, message):
        if message.topic == "objects_changed" and message["object_type"] == "event":
            self.refresh_events(message["objects"])
