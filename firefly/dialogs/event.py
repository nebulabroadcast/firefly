import time
import datetime

from firefly import *

__all__ = ["event_dialog"]


default_meta_set = [
        ["start", {}],
        ["title", {}],
        ["subtitle", {}],
        ["description", {}],
        ["color", {}]
    ]

class EventDialog(QDialog):
    def __init__(self,  parent, **kwargs):
        super(EventDialog, self).__init__(parent)
        self.setWindowTitle("Scheduler")
        self.kwargs = kwargs
        self.setStyleSheet(app_skin)

        self.event = kwargs.get("event", Event())
        self.accepted = False
        self.can_edit = user.has_right("scheduler_edit", self.event["id_channel"])

        for key in ["start", "id_channel"]:
            if kwargs.get(key, False):
                self.event[key] = kwargs[key]

        keys = config["playout_channels"][self.event["id_channel"]].get("meta_set", default_meta_set)

        if "asset" in self.kwargs:
            asset = self.kwargs["asset"]
            for key in [k for k in meta_types if meta_types[k]["ns"] == "m"]:
                if not key in asset.meta:
                    continue
                self.event[key] = asset[key]

        self.form = MetaEditor(self, keys)
        for key in self.form.keys():
            self.form[key] = self.event[key]

        if not self.can_edit:
            self.form.setEnabled(False)


        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.on_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.form, 2)
        layout.addWidget(buttons)
        self.setLayout(layout)


    def closeEvent(self, event):
        event.accept()

    def on_cancel(self):
        self.close()

    def on_accept(self):
        if not self.can_edit:
            self.close()
            return

        meta = self.form.meta
        for key in ["id_channel", "start"]:
            meta[key] = self.event[key]

        for key in meta:
            value = meta[key]
            self.event[key] = value     # use event as a validator
            meta[key] = self.event[key]

        result = api.schedule(
                id_channel=self.event["id_channel"],
                events=[meta]
            )

        if result.is_error:
            logging.error(result.message)

        self.accepted = True
        self.close()



def event_dialog(**kwargs):
    dlg = EventDialog(None, **kwargs)
    dlg.exec_()
    return dlg.accepted

