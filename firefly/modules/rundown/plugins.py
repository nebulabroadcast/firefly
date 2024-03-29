import functools

from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QPushButton, QTabWidget, QWidget

import firefly
from firefly.api import api
from firefly.components.input_combo import InputCombo
from firefly.components.input_text import InputText
from firefly.log import log


class PlayoutPlugin(QWidget):
    def __init__(self, parent, data):
        super(PlayoutPlugin, self).__init__(parent)

        self.id_channel = parent.id_channel
        self.name = data["name"]
        self.title = data["title"]
        self.slots = {}
        self.buttons = []

        button_layout = QHBoxLayout()
        layout = QFormLayout()

        for i, slot in enumerate(data.get("slots", [])):
            slot_type = slot["type"]
            slot_name = slot["name"]
            slot_title = slot.get("title", slot_name)

            if slot_type == "action":
                self.buttons.append(QPushButton(slot_title))
                self.buttons[-1].clicked.connect(
                    functools.partial(self.execute, slot_name)
                )
                button_layout.addWidget(self.buttons[-1])
                continue

            if slot_type == "text":
                self.slots[slot_name] = InputText(self)
            elif slot_type == "select":
                options = slot.get("options", [])
                print(options)
                if not slot["options"]:
                    continue
                self.slots[slot_name] = InputCombo(self, options=options)
            else:
                continue
            layout.addRow(slot_title, self.slots[slot_name])

        if self.buttons:
            layout.addRow("", button_layout)
        self.setLayout(layout)

    def execute(self, action: str):
        data = {}
        for slot in self.slots:
            data[slot] = self.slots[slot].get_value()

        response = api.playout(
            action="plugin_exec",
            id_channel=self.id_channel,
            payload={
                "name": self.name,
                "action": action,
                "data": data,
            },
        )
        if response:
            log.info(f"{self.title} action '{action}' executed succesfully.")
        else:
            log.error(
                f"[PLUGINS] Plugin error {response.response}\n\n{response.message}"
            )


class PlayoutPlugins(QTabWidget):
    def __init__(self, parent):
        super(PlayoutPlugins, self).__init__(parent)
        self.plugins = []

    @property
    def id_channel(self):
        return self.parent().id_channel

    def load(self):
        if not firefly.user.can("mcr", self.id_channel):
            return

        log.debug("[PLUGINS] Loading playout plugins")
        for idx in reversed(range(self.count())):
            widget = self.widget(idx)
            self.removeTab(idx)
            widget.deleteLater()

        response = api.playout(action="plugin_list", id_channel=self.id_channel)
        if not response:
            log.error(f"[PLUGINS] Unable to load playout plugins:\n{response.message}")
            return

        for plugin in response.get("plugins") or []:
            self.plugins.append(PlayoutPlugin(self, plugin))
            self.addTab(self.plugins[-1], plugin.get("title", "unknown"))
