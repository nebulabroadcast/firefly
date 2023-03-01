from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSpinBox


class InputInteger(QSpinBox):
    def __init__(self, parent, value, **kwargs):
        super().__init__(parent)
        self._default_value = value

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimum(kwargs.get("min", 0))
        self.setMaximum(kwargs.get("max", 99999))
        if kwargs.get("hide_null"):
            self.setMinimum(0)
            self.setSpecialValueText(" ")
        self.setSingleStep(1)

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setValue(int(value))
        self.default = self.get_value()

    def get_value(self):
        return int(self.value())
