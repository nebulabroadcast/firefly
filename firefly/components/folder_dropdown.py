from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QComboBox

import firefly
from firefly.qt import pixlib


class FolderDropdown(QComboBox):
    folder_changed = Signal(int)

    def __init__(self, parent, value=None):
        super().__init__(parent)
        self._value = value
        self._default_value = value

        self._folder_ids = []

        for i, folder in enumerate(firefly.settings.folders):
            self.addItem(folder.name)
            self.setItemIcon(i, QIcon(pixlib[f"folder_{folder.id}"]))
            self._folder_ids.append(folder.id)

        self.set_value(value)
        self.currentIndexChanged.connect(self._on_change)

    def setReadOnly(self, val: bool) -> None:
        self.setEnabled(not val)

    def _on_change(self, index: int) -> None:
        self._value = self._folder_ids[index]
        self.folder_changed.emit(self._value)

    def set_value(self, value: int) -> None:
        if value == self.get_value():
            return
        if not value:
            return
        self._value = value
        for i, val in enumerate(self._folder_ids):
            if val == value:
                self.setCurrentIndex(i)
                break
        else:
            self.setCurrentIndex(0)
            self._value = self._folder_ids[0]

    def get_value(self) -> int:
        return self._value
