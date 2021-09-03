import functools

from nx import *
from firefly.common import *

from nebulacore.meta_format import format_select, format_list

from .comboutils import *


class FireflyRadio(QWidget):
    def __init__(self, parent, **kwargs):
        super(FireflyRadio, self).__init__(parent)
        self.cdata = []
        self.current_index = -1
        self.buttons = []
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)
        if kwargs.get("data", []):
            self.set_data(kwargs["data"])
        self.default = self.get_value()


    def clear(self):
        for i, button in enumerate(self.buttons):
            button.deleteLater()
            self.layout.removeWidget(button)
        self.current_index = -1
        self.buttons = []

    def auto_data(self, key, id_folder=0):
        data = format_select(key, None, result="full", id_folder=id_folder)
        self.set_data(data)

    def set_data(self, data):
        self.clear()
        self.current_index = -1
        i = 0
        for row in data:
            value = row["value"]
            alias = row.get("alias", row["value"])
            description = row.get("description") or alias or "(No value)"
            if not row.get("value"):
                continue
            if row["role"] == "hidden":
                continue
            self.cdata.append(row["value"])

            self.buttons.append(QPushButton(alias))
            self.buttons[-1].setToolTip(f"<p>{description}</p>")
            self.buttons[-1].setCheckable(row["role"] in ["option", "header"])
            self.buttons[-1].setAutoExclusive(True)
            self.buttons[-1].clicked.connect(functools.partial(self.switch, i))
            self.layout.addWidget(self.buttons[-1])
            i+= 1


    def switch(self, index):
        self.current_index = index

    def set_value(self, value):
        value = str(value)

        if not value and self.cdata and self.cdata[0] == "0":
            value = "0"

        for i, val in enumerate(self.cdata):
            if val == value:
                self.buttons[i].setChecked(True)
                self.current_index = i
                break
        else:
            self.current_index = -1
            for button in self.buttons:
                button.setAutoExclusive(False);
                button.setChecked(False);
                button.setAutoExclusive(True);
        self.default = self.get_value()

    def get_value(self):
        if self.current_index == -1:
            return ""
        return str(self.cdata[self.current_index])

    def setReadOnly(self, val):
        for w in self.buttons:
            w.setEnabled(not val)


class FireflySelect(QComboBox):
    def __init__(self, parent, **kwargs):
        super(FireflySelect, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.cdata = []
        if kwargs.get("data", []):
            self.set_data(kwargs["data"])
        self.default = self.get_value()

        delegate = ComboMenuDelegate(self)
        self.setItemDelegate(delegate)

    def wheelEvent(self, event):
        if self.hasFocus():
            super(FireflySelect, self).wheelEvent(event)
        else:
            event.ignore()

    def setReadOnly(self, val):
        self.setEnabled(not val)

    def auto_data(self, key, id_folder=0):
        data = format_select(key, None, result="full", id_folder=id_folder)
        self.set_data(data)

    def set_data(self, data):
        self.clear()
        self.cdata = []
        i = 0
        for row in data:
            value = row["value"]
            alias = row.get("alias", row["value"])
            description = row.get("description") or alias or "(No value)"
            indent = row.get("indent", 0)
            role = row.get("role", "option")

            if role == "hidden":
                continue

            self.addItem(alias)
            self.cdata.append(value)

            self.setItemData(i, indent ,Qt.UserRole)
            self.setItemData(i, f"<p>{description}</p>", Qt.ToolTipRole)

            if role == "header":
                self.setItemData(i, fonts["bold"], Qt.FontRole)

            elif role == "label":
                item = self.model().item(i)
                item.setEnabled(False)
                self.setItemData(i, fonts["boldunderline"], Qt.FontRole)

            if row.get("selected"):
                self.setCurrentIndex(i)
            i+=1

    def set_value(self, value):
        if value == self.get_value():
            return
        if not value and self.cdata and self.cdata[0] == "0":
            self.setCurrentIndex(0)
            return
        if not value:
            return
        for i, val in enumerate(self.cdata):
            if val == value:
                self.setCurrentIndex(i)
                break
        else:
            self.setCurrentIndex(-1)
        self.default = self.get_value()

    def get_value(self):
        if self.currentIndex() == -1:
            return ""
        return self.cdata[self.currentIndex()]


class FireflyList(CheckComboBox):
    def __init__(self, parent, **kwargs):
        super(FireflyList, self).__init__(parent, placeholderText="")
        self.cdata = []
        if kwargs.get("data", []):
            self.set_data(kwargs["data"])
        self.default = self.get_value()

    def setReadOnly(self, val):
        self.setEnabled(not val)

    def auto_data(self, key, id_folder=0):
        data = format_list(key, [], result="full", id_folder=id_folder)
        self.set_data(data)

    def set_data(self, data):
        self.clear()
        self.cdata = []
        i = 0
        for row in data:
            value = row["value"]
            alias = row.get("alias", row["value"])
            description = row.get("description") or alias or "(No value)"
            indent = row.get("indent", 0)
            role = row.get("role", "option")

            if role == "hidden":
                continue

            self.addItem(alias)
            self.cdata.append(value)

            self.setItemData(i, indent, Qt.UserRole)

            self.setItemData(i, f"<p>{description}</p>", Qt.ToolTipRole)

            if row["role"] == "label":
                item = self.model().item(i)
                self.setItemData(i, fonts["boldunderline"], Qt.FontRole)
                item.setEnabled(False)
            else:
                self.model().item(i).setCheckable(True)
                if row["role"] == "header":
                    self.setItemData(i, fonts["bold"], Qt.FontRole)
                self.setItemCheckState(i, row.get("selected"))
            i+=1

    def set_value(self, value):
        if type(value) == str:
            value = [value]
        value = [str(v) for v in value]
        for i, val in enumerate(self.cdata):
            self.setItemCheckState(i, val in value)
        self.default = self.get_value()

    def get_value(self):
        result = []
        for i, val in enumerate(self.cdata):
            if self.itemCheckState(i):
                result.append(val)
        return result
