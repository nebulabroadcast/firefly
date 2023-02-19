import functools

from typing import Any
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout

import firefly


class InputRadio(QWidget):
    def __init__(self, parent, value: str | None = None, **kwargs):
        super().__init__(parent)

        self._value = value
        self._default_value = value

        self._options = []
        if urn := kwargs.get("cs"):
            _filter = kwargs.get("filter")

            for opt_value, csmeta in firefly.settings.cs.get(urn, {}).items():
                if _filter := kwargs.get("filter"):
                    if not filter_match(_filter, opt_value):
                        continue

                if csmeta.get("role") in ["hidden", "header"]:
                    continue

                self._options.append(
                    {
                        "value": value,
                        "title": csmeta.get("title", opt_value),
                        "description": csmeta.get("description", opt_value),
                    }
                )

        self._current_index = None
        self._buttons = []
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        if self._options:
            self.build_options()

    def clear(self):
        for i, button in enumerate(self._buttons):
            button.deleteLater()
            self._layout.removeWidget(button)
        self._current_index = None
        self._buttons = []

    def auto_options(self, key, id_folder=0):
        # TODO
        self.set_options([])

    def build_options(self):
        self.clear()
        self._current_index = None
        i = 0
        for row in self._options:
            title = row.get("title", row["value"])
            description = row.get("description")
            self._buttons.append(QPushButton(title))
            if description:
                self._buttons[-1].setToolTip(f"<p>{description}</p>")
            self._buttons[-1].setCheckable(True)
            self._buttons[-1].setAutoExclusive(True)
            self._buttons[-1].clicked.connect(functools.partial(self.switch, i))
            self._layout.addWidget(self._buttons[-1])
            if self._value == row["value"]:
                self._current_index = i
                self._buttons[-1].setChecked(True)
            i += 1

    def set_options(self, options: list[dict[str, Any]]) -> None:
        self._options = options
        self.build_options()

    def switch(self, index: int) -> None:
        self._current_index = index
        self._value = self._options[index]["value"]

    def set_value(self, value: str) -> None:
        if value == self._value:
            return

        if not value and self._options and self._options[0]["value"] == "0":
            value = "0"

        self._value = value
        self._current_index = None
        for i, row in enumerate(self._options):
            if row["value"] == value:
                self._current_index = i
                self._buttons[i].setChecked(True)
                break
        else:
            self._current_index = None
            for button in self._buttons:
                button.setAutoExclusive(False)
                button.setChecked(False)
                button.setAutoExclusive(True)

    def get_value(self) -> str | None:
        return self._value

    def setReadOnly(self, val: bool) -> None:
        for w in self._buttons:
            w.setEnabled(not val)
