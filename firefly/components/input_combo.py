from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox

import firefly
from firefly.metadata.utils import filter_match


class InputCombo(QComboBox):
    selection_changed = Signal(str)

    def __init__(self, parent, value=None, **kwargs):
        super().__init__(parent)
        self._value = value
        self._original_value = value
        self._options = []

        self.set_field_options(**kwargs)
        self.set_value(value)
        self.currentIndexChanged.connect(self._on_change)

    def set_field_options(self, **kwargs) -> None:
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
                        "value": opt_value,
                        "title": csmeta.get("title", opt_value),
                        "description": csmeta.get("description", opt_value),
                    }
                )
        elif options := kwargs.get("options"):
            self._options = options

        self.clear()
        for opt in self._options:
            self.addItem(opt["title"])

    def setReadOnly(self, val: bool) -> None:
        self.setEnabled(not val)

    def _on_change(self, index: int) -> None:
        self._value = self._options[index]["value"]
        self.selection_changed.emit(self._value)

    def set_value(self, value: int) -> None:
        if value == self.get_value():
            return
        self._value = value
        for i, val in enumerate(self._options):
            if val["value"] == value:
                self.setCurrentIndex(i)
                break
        else:
            self.setCurrentIndex(-1)
            self._value = None

    def get_value(self) -> int:
        return self._value
