import copy
import json

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QWidget, QLabel

from firefly.metadata import meta_types
from firefly.settings import FolderField

from .input_color import InputColor
from .input_text import InputText
from .input_textarea import InputTextarea
from .input_timecode import InputTimecode
from .input_datetime import InputDatetime
from .input_switch import InputSwitch
from .input_radio import InputRadio
from .input_select import InputSelect
from .input_list import InputList


class NotImplementeWidget(QLabel):
    def __init__(self, parent, value=None, **kwargs):
        super(NotImplementeWidget, self).__init__(parent)
        self.set_value(value)
        self.default = value

    def set_value(self, value):
        self.setText(json.dumps(value))

    def get_value(self):
        return self.default

    def set_options(self, options):
        pass

    def setReadOnly(self, value):
        pass


editor_map = {
    "string": InputText,
    "text": InputTextarea,
    "timecode": InputTimecode,
    "datetime": InputDatetime,
    "color": InputColor,
    "boolean": InputSwitch,
    "select": InputSelect,
    "list": InputList,
}


class MetadataForm(QWidget):
    def __init__(
        self,
        parent,
        fields: list[FolderField],
        data: dict[str, Any],
    ):
        super().__init__(parent)
        self.fields = fields
        self.original_values = copy.deepcopy(data)

        layout = QGridLayout()
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 3)
        layout.setColumnMinimumWidth(0, 150)

        self.inputs = {}
        self.labels = {}

        i = 0
        for field in fields:
            if field.name not in meta_types:
                continue
            meta_type = meta_types[field.name]

            key_label = meta_type.title
            key_description = meta_type.description
            key_class = meta_type.type

            key_settings = meta_type.dict()
            key_settings.update(field.dict(exclude_none=True, exclude_unset=True))

            label = QLabel(key_label, self)
            label.setStyleSheet("padding-top:9px;")

            if key_description:
                label.setToolTip(key_description)

            if key_settings.get("mode") == "radio":
                input_class = InputRadio
            else:
                input_class = editor_map.get(key_class, NotImplementeWidget)

            self.inputs[field.name] = input_class(
                self,
                self.original_values.get(field.name),
                **key_settings,
            )
            self.labels[field.name] = label

            layout.addWidget(self.labels[field.name], i, 0, Qt.AlignmentFlag.AlignTop)
            layout.addWidget(self.inputs[field.name], i, 1)

            i += 1

        self.setLayout(layout)

    def keys(self):
        return self.inputs.keys()

    def __getitem__(self, key):
        return self.inputs[key].get_value()

    def __setitem__(self, key, value):
        self.inputs[key].set_value(value)

    def setEnabled(self, stat):
        for w in self.inputs:
            self.inputs[w].setReadOnly(not stat)

    @property
    def meta(self):
        result = copy.deepcopy(self.original_values)
        for field in self.fields:
            if field.name not in self.inputs:
                continue
            result[field.name] = self.inputs[field.name].get_value()
        return result

    @property
    def changed(self) -> list[str]:
        """return list of changed fields"""
        result = []
        for key, value in self.meta.items():
            if value != self.original_values.get(key):
                result.append(key)
        return result

    def set_defaults(self):
        """Assume current values are defaults and form is unchanged."""
        self.original_values = self.meta
