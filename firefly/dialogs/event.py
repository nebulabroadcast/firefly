from nxtools import logging

import firefly

from firefly.api import api
from firefly.objects import Event
from firefly.widgets import MetaEditor
from firefly.settings import FolderField
from firefly.qt import Qt, QDialog, QDialogButtonBox, QVBoxLayout, app_skin


default_fields = [
    FolderField(name="start"),
    FolderField(name="title"),
    FolderField(name="subtitle"),
    FolderField(name="description"),
    FolderField(name="color"),
]


class EventDialog(QDialog):
    def __init__(self, parent, **kwargs):
        super(EventDialog, self).__init__(parent)
        self.setWindowTitle("Scheduler")
        self.kwargs = kwargs
        self.setStyleSheet(app_skin)

        self.event = kwargs.get("event", Event())
        for key in ["start", "id_channel"]:
            if (value := kwargs.get(key)) is not None:
                self.event[key] = value

        self.result = None
        self.can_edit = firefly.user.can("scheduler_edit", self.event["id_channel"])
        self.date = kwargs["date"]

        playout_config = firefly.settings.get_playout_channel(self.event["id_channel"])

        fields = playout_config.fields or default_fields

        if (asset := self.kwargs.get("asset")) is not None:
            for field in fields:
                if field.name in asset.meta:
                    self.event[field.name] = asset.meta[field.name]

        self.form = MetaEditor(self, fields)
        for key in self.form.keys():
            self.form[key] = self.event[key]

        if not self.can_edit:
            self.form.setEnabled(False)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.on_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.form, 2)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def closeEvent(self, evt):
        evt.accept()

    def on_cancel(self):
        self.close()

    def on_accept(self):
        if not self.can_edit:
            self.close()
            return

        meta = self.form.meta
        for key in ["id_channel", "start", "id"]:
            if key not in meta:
                meta[key] = self.event[key]
        meta["id_channel"] = self.event["id_channel"]

        response = api.scheduler(
            id_channel=self.event["id_channel"],
            date=self.date,
            events=[
                {
                    "id": self.event["id"],
                    "start": self.event["start"],
                    "meta": meta,
                }
            ],
        )

        if not response:
            logging.error("Scheduler dialog response", response.message)

        self.result = response
        self.close()


def show_event_dialog(parent=None, **kwargs):
    dlg = EventDialog(parent, **kwargs)
    dlg.exec()
    return dlg.result
