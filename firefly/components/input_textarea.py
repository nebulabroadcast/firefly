from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QTextEdit


class InputTextarea(QTextEdit):
    def __init__(self, parent, value: str | None = None, **kwargs):
        super().__init__(parent)
        self.original_value = value
        if value:
            self.setText(str(value))

        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed_font.setStyleHint(QFont.StyleHint.Monospace)
        self.setCurrentFont(fixed_font)
        self.setTabChangesFocus(True)

    def set_value(self, value: str | None = None) -> None:
        if value == self.get_value():
            return
        if value:
            self.setText(str(value))
        else:
            self.clear()

    def get_value(self) -> str:
        return self.toPlainText()
