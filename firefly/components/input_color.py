from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QPushButton


class InputColor(QPushButton):
    def __init__(self, parent, value=None, **kwargs):
        super().__init__(parent)
        self._original_value = value
        self._value = value
        self.clicked.connect(self.execute)

    def execute(self):
        color = int(QColorDialog.getColor(QColor(self._value)).rgb())
        self.set_value(color)

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value
        self.setStyleSheet(f"background-color: #{self.color:06x}")

    def setReadOnly(self, stat):
        self.setEnabled(not stat)
