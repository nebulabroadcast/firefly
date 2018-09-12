import functools

from firefly.common import *
from firefly.widgets import *

class PlayoutPlugin(QWidget):
    def __init__(self, parent, data):
        super(PlayoutPlugin, self).__init__(parent)

        self.id_channel = parent.id_channel
        self.id_plugin = data["id"]
        self.title = data["title"]
        self.slots = {}

        self.buttons = []
        button_layout = QHBoxLayout()
        layout = QFormLayout()

        for i, slot in enumerate(data.get("slots", [])):
            slot_type = slot["type"]
            slot_name = slot["name"]

            if slot_type == "action":
                self.buttons.append(QPushButton(slot["title"]))
                self.buttons[-1].clicked.connect(
                    functools.partial(
                            self.execute,
                            slot_name
                        )
                    )
                button_layout.addWidget(self.buttons[-1])
                continue

            if slot_type == "text":
                self.slots[slot_name] = FireflyString(self)
            elif slot_type == "select":
                if not slot["values"]:
                    continue
                self.slots[slot_name] = FireflySelect(self, data=slot["values"])
                self.slots[slot_name].set_value(min([r[0] for r in slot["values"]]))
            else:
                continue
            layout.addRow(slot["title"], self.slots[slot_name])

        if self.buttons:
            layout.addRow("", button_layout)
        self.setLayout(layout)


    def execute(self, name):
        value = False
        data = {}
        for slot in self.slots:
            data[slot] = self.slots[slot].get_value()

        response = api.playout(
                action="plugin_exec",
                id_channel=self.id_channel,
                id_plugin=self.id_plugin,
                action_name=name,
                data=json.dumps(data)
            )
        if response.is_error:
            logging.error("Plugin error {}\n\n{}".format(response.response, response.message))
        else:
            logging.info("{} action '{}' executed succesfully.".format(self.title, name))



class PlayoutPlugins(QTabWidget):
    def __init__(self, parent):
        super(PlayoutPlugins, self).__init__(parent)
        self.plugins = []

    @property
    def id_channel(self):
        return self.parent().id_channel

    def load(self):
        logging.debug("Loading playout plugins")
        for idx in reversed(range(self.count())):
            widget = self.widget(idx)
            self.removeTab(idx)
            widget.deleteLater()

        response = api.playout(action="plugin_list", id_channel=self.id_channel)
        if response.is_error:
            logging.error("Unable to load playout plugins:\n{}".format(response.message))
            return

        for plugin in response.data:
            self.plugins.append(PlayoutPlugin(self, plugin))
            self.addTab(self.plugins[-1], plugin["title"])
