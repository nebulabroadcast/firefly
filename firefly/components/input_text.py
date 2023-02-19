from PySide6.QtWidgets import QLineEdit


class InputText(QLineEdit):
    def __init__(self, parent, value: str | None = None, **kwargs):
        super().__init__(parent)
        self._original_value = value
        if value:
            self.setText(value)

    def set_value(self, value: str) -> None:
        if value == self.get_value():
            return
        if value:
            self.setText(str(value))
        else:
            self.clear()

    def get_value(self):
        return self.text()
