from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout

import firefly
from firefly.api import api
from firefly.components.form import MetadataForm
from firefly.log import log
from firefly.objects import Event
from firefly.qt import app_skin
from firefly.settings import FolderField

default_fields = [
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
        self.date = kwargs.get("date")

        playout_config = firefly.settings.get_playout_channel(self.event["id_channel"])
        fields = [FolderField(name="start", required=True)]
        if playout_config.fields:
            fields.extend(playout_config.fields)
        else:
            fields.extend(default_fields)

        if (asset := self.kwargs.get("asset")) is not None:
            for field in fields:
                if field.name in asset.meta:
                    self.event[field.name] = asset.meta[field.name]

        self.form = MetadataForm(self, fields, self.event.meta)

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

        if not self.form["start"]:
            firefly.log.error("Event must have a start time")
            return

        for key in self.form.changed:
            self.event[key] = self.form[key]

        response = api.scheduler(
            id_channel=self.event["id_channel"],
            date=self.date,
            events=[
                {
                    "id": self.event["id"],
                    "start": self.event["start"],
                    "meta": self.event.meta,
                }
            ],
        )

        if not response:
            log.error("Scheduler dialog response", response.message)

        self.result = response
        self.close()


def show_event_dialog(parent=None, **kwargs):
    dlg = EventDialog(parent, **kwargs)
    dlg.exec()
    return dlg.result
