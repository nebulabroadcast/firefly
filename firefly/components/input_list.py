from PySide6.QtWidgets import QLineEdit

import firefly
from firefly.metadata.utils import filter_match


class InputList(QLineEdit):
    def __init__(self, parent, value: list[str] | None = None, **kwargs):
        super().__init__(parent)

        self._value = value
        self._original_value = value
        self._options = []

        self.setReadOnly(True)

        self.set_field_options(**kwargs)
        self.set_value(value)

    def setReadOnly(self, value: bool) -> None:
        super().setReadOnly(True)

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

    def set_value(self, value: str) -> None:
        if value:
            result = []
            for opt in self._options:
                if opt["value"] in value:
                    result.append(opt["title"])
            self.setText(", ".join(result))
        else:
            self.setText("")
        self._value = value

    def get_value(self):
        self._value
