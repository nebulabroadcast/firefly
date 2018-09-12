import time
import datetime

from firefly import *

def event_toolbar(wnd):
    toolbar = QToolBar(wnd)
    toolbar.setMovable(False)
    toolbar.setFloatable(False)

    toolbar.addWidget(ToolBarStretcher(toolbar))

    action_accept = QAction(QIcon(pix_lib["accept"]), 'Accept changes', wnd)
    action_accept.setShortcut('Ctrl+S')
    action_accept.triggered.connect(wnd.on_accept)
    toolbar.addAction(action_accept)

    action_cancel = QAction(QIcon(pix_lib["cancel"]), 'Cancel', wnd)
    action_cancel.setShortcut('ESC')
    action_cancel.triggered.connect(wnd.on_cancel)
    toolbar.addAction(action_cancel)

    return toolbar


class EventDialog(QDialog):
    def __init__(self,  parent, **kwargs):
        super(EventDialog, self).__init__(parent)
        self.setWindowTitle("Scheduler")
        self.kwargs = kwargs
        self.setStyleSheet(app_skin)
        self.toolbar = event_toolbar(self)

        default_keys = [
                ["start", {}],
                ["title", {}],
                ["subtitle", {}],
                ["description", {}]
            ]
        keys = default_keys #TODO: config

        self.event = kwargs.get("event", Event())

        for key in ["start", "id_channel"]:
            if kwargs.get(key, False):
                self.event[key] = kwargs[key]

        if "asset" in self.kwargs:
            asset = self.kwargs["asset"]
            for key in [k for k in meta_types if meta_types[k]["ns"] == "m"]:
                if not key in asset.meta:
                    continue
                self.event[key] = asset[key]

        self.form = MetaEditor(self, keys)
        for key in self.form.keys():
            if self.event[key]:
                self.form[key] = self.event[key]

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        layout.addWidget(self.toolbar, 1)
        layout.addWidget(self.form, 2)
        self.setLayout(layout)


    def closeEvent(self, event):
        event.accept()

    def on_cancel(self):
        self.close()

    def on_accept(self):
        meta = self.form.meta
        for key in meta:
            value = meta[key]
            if value:
                self.event[key] = value

        result = api.schedule(
                id_channel=self.event["id_channel"],
                events=[self.event.meta]
            )

        if result.is_error:
            logging.error(result.message)

        self.close()
