from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class ClickableLineEdit(QLineEdit):
    activated = Signal()

    def focusInEvent(self, event):
        self.activated.emit()


class DateTimeEdit(QDateTimeEdit):
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return:
            self.editingFinished.emit()
            event.ignore()
        else:
            super().keyPressEvent(event)


class InputDatetime(QWidget):
    def __init__(self, parent, value=None, **kwargs):
        super().__init__(parent)
        self._original_value = int(value) if value else None
        self._read_only = False
        self.required = kwargs.get("required", False)

        self.display = ClickableLineEdit(self)
        self.display.setReadOnly(True)
        self.display.activated.connect(self.start_edit)

        self.editor = QDateTimeEdit(self)
        self.editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.editor.setCalendarPopup(True)
        self.editor.dateTimeChanged.connect(self.on_datetime_changed)
        self.editor.editingFinished.connect(self.end_edit)
        self.editor.hide()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.display, 1)
        layout.addWidget(self.editor, 1)

        if not self.required:
            self.clear_button = QPushButton(self)
            self.clear_button.setText("Clear")
            self.clear_button.clicked.connect(self.clear_value)
            layout.addWidget(self.clear_button, 0)
        else:
            self.clear_button = None

        self.setLayout(layout)
        self.set_value(value)

    def clear_value(self):
        self.set_value(None)

    def start_edit(self):
        if self._read_only:
            return
        self.display.hide()
        self.editor.show()
        self.editor.setFocus()

    def end_edit(self):
        self.editor.hide()
        self.display.show()

    def on_datetime_changed(self, value):
        timestamp = int(self.editor.dateTime().toSecsSinceEpoch())
        self.display.setText(self.editor.text())
        self._value = timestamp

    def set_value(self, value):
        if not value:
            self.display.setText("")
            self._value = None
            return
        self._value = int(value)
        self.editor.setDateTime(QDateTime.fromSecsSinceEpoch(self._value))
        self.display.setText(self.editor.text())

    def get_value(self):
        return self._value

    def setReadOnly(self, value):
        self._read_only = value
        self.end_edit()
        if self.clear_button:
            self.clear_button.setEnabled(not value)
