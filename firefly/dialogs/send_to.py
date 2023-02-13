import functools

from nxtools import logging

from firefly.api import api
from firefly.widgets import ActionButton
from firefly.qt import Qt, QDialog, QVBoxLayout, QCheckBox, QApplication


class SendToDialog(QDialog):
    def __init__(self, parent, title, actions=list[tuple[int, str]]):
        super(SendToDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowTitle(title)

        layout = QVBoxLayout()
        for id_action, title in actions:
            btn_send = ActionButton(title)
            btn_send.clicked.connect(functools.partial(self.on_send, id_action))
            layout.addWidget(btn_send, 1)

        self.restart_existing = QCheckBox("Restart existing actions", self)
        self.restart_existing.setChecked(True)
        layout.addWidget(self.restart_existing, 0)

        self.restart_running = QCheckBox("Restart running actions", self)
        self.restart_running.setChecked(False)
        layout.addWidget(self.restart_running, 0)

        self.setLayout(layout)
        self.setMinimumWidth(400)

        self.id_action = None

    def on_send(self, id_action):
        self.id_action = id_action
        self.close()

    def handle_query(self, msg):
        QApplication.processEvents()


def show_send_to_dialog(parent=None, objects: list | None = None):
    if not objects:
        return

    # Create list of asset ids

    asset_ids = []
    for obj in objects:
        if obj.object_type == "asset":
            asset_ids.append(obj.id)
        elif obj.object_type == "item" and obj["id_asset"]:
            asset_ids.append(obj["id_asset"])

    # Build dialog title

    if len(objects) == 1:
        what = objects[0]["title"]
    else:
        what = f"{len(objects)} objects"
    title = f"Send {what} to..."

    # Get a list of actions

    response = api.actions(ids=asset_ids)

    if not response:
        logging.error(response.message)
        return

    actions = []
    for action in response["actions"]:
        actions.append((action["id"], action["name"]))

    if not actions:
        logging.error("No actions available")
        return

    # Execute the dialog

    dlg = SendToDialog(parent, title, actions)
    dlg.exec()

    if not dlg.id_action:
        return

    # Run the send query

    print("sending to", dlg.id_action)

    QApplication.processEvents()
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    response = api.send(
        ids=asset_ids,
        id_action=dlg.id_action,
        restart_existing=dlg.restart_existing.isChecked(),
        restart_running=dlg.restart_running.isChecked(),
    )
    QApplication.restoreOverrideCursor()
    if not response:
        logging.error(response.message)
