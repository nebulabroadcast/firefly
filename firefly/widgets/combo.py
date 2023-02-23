from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox

from firefly.qt import fontlib


def format_select(*args, **kwargs):
    return {}


format_list = format_select


class FireflySelect(QComboBox):
    def __init__(self, parent, options=None, **kwargs):
        super(FireflySelect, self).__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.cdata = []
        if options is not None:
            self.set_options(options)
        self.default = self.get_value()

    def wheelEvent(self, event):
        if self.hasFocus():
            super(FireflySelect, self).wheelEvent(event)
        else:
            event.ignore()

    def setReadOnly(self, val):
        self.setEnabled(not val)

    def auto_options(self, key, id_folder=0):
        # TODO
        self.set_options([])

    def set_options(self, options):
        self.clear()
        self.cdata = []
        i = 0
        for row in options:
            value = row["value"]
            title = row.get("title", str(row["value"]))
            description = row.get("description") or title or "(No value)"
            indent = row.get("indent", 0)
            role = row.get("role", "option")

            if role == "hidden":
                continue

            self.addItem(title)
            self.cdata.append(value)

            self.setItemData(i, indent, Qt.ItemDataRole.UserRole)
            self.setItemData(i, f"<p>{description}</p>", Qt.ItemDataRole.ToolTipRole)

            if role == "header":
                self.setItemData(i, fontlib["bold"], Qt.ItemDataRole.FontRole)

            elif role == "label":
                item = self.model().item(i)
                item.setEnabled(False)
                self.setItemData(i, fontlib["boldunderline"], Qt.ItemDataRole.FontRole)

            if row.get("selected"):
                self.setCurrentIndex(i)
            i += 1

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
