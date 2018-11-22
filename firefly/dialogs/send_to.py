import functools
from firefly import *

__all__ = ["send_to_dialog"]


class SendToDialog(QDialog):
    def __init__(self,  parent, objects=[]):
        super(SendToDialog, self).__init__(parent)
        self.objects = list(objects)
        self.setModal(True)

        if len(self.objects) == 1:
            what = self.objects[0]["title"]
        else:
            what = "{} objects".format(len(self.objects))

        self.setWindowTitle("Send {} to...".format(what))

        self.actions = []
        response = api.actions(ids=self.assets)
        if response.is_error:
            logging.error(response.message)
            self.close()
        else:
            layout = QVBoxLayout()
            for id_action, title in response.data:
                btn_send = ActionButton(title)
                btn_send.clicked.connect(functools.partial(self.on_send, id_action))
                layout.addWidget(btn_send,1)

            self.restart_existing = QCheckBox('Restart existing actions', self)
            self.restart_existing.setChecked(True)
            layout.addWidget(self.restart_existing, 0)

            self.restart_running = QCheckBox('Restart running actions', self)
            self.restart_running.setChecked(False)
            layout.addWidget(self.restart_running, 0)

            self.setLayout(layout)
            self.setMinimumWidth(400)

    @property
    def assets(self):
        result = []
        for obj in self.objects:
            if obj.object_type == "asset":
                result.append(obj.id)
            elif obj.object_type == "item" and obj["id_asset"]:
                result.append(obj["id_asset"])
        return result

    def on_send(self, id_action):
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        response = api.send(
                id_action=id_action,
                ids=self.assets,
                restart_existing=self.restart_existing.isChecked(),
                restart_running=self.restart_running.isChecked()
            )
        QApplication.restoreOverrideCursor()
        if response.is_error:
            logging.error(response.message)
        else:
            self.close()

    def handle_query(self, msg):
        QApplication.processEvents()



def send_to_dialog(objects):
    dlg = SendToDialog(None, objects)
    dlg.exec_()
