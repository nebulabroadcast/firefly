import re

from nxtools import s2tc, tc2s
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QLineEdit


class InputTimecode(QLineEdit):
    def __init__(self, parent=None, value=None, **kwargs):
        super().__init__(parent)

        self._fps = kwargs.get("fps", 25)
        self._value = value
        self._original_value = value

        self.setPlaceholderText("--:--:--:--")
        self.setMaxLength(11)
        self.setFixedWidth(110)
        self.setAlignment(Qt.AlignCenter)

        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed_font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(fixed_font)

        if value:
            self.setText(s2tc(value, self._fps))
        self._text = self.text()

        self.editingFinished.connect(self.onSubmit)
        self.textChanged.connect(self.onChangeHandler)
        self.returnPressed.connect(self.onSubmit)

    def focusInEvent(self, event):
        QTimer.singleShot(1, self.selectAll)

    def onChangeHandler(self, text):
        text = re.sub(r"[^0-9:]", "", text)
        if len(text) > 11:
            self.setText(self._text)
            return

        text = re.sub(r"[^0-9]", "", text)
        if len(text) > 2:
            text = text[:-2] + ":" + text[-2:]
        if len(text) > 5:
            text = text[:-5] + ":" + text[-5:]
        if len(text) > 8:
            text = text[:-8] + ":" + text[-8:]

        self._text = text
        self.setText(text)

    def onSubmit(self):
        text = self.text()
        if not text:
            self._value = None
            return
        text = text.replace(":", "")
        text = text.zfill(8)
        text = ":".join([text[i : i + 2] for i in range(0, len(text), 2)])  # noqa: E203
        self.setText(text)
        self._value = tc2s(text, self._fps)

    def get_value(self) -> float | None:
        return self._value

    def set_value(self, value: float | None) -> None:
        if value == self._value:
            return

        self._value = value
        if value:
            self.setText(s2tc(value, self._fps))
        else:
            self.setText("")
