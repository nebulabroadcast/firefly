import copy

from nx import *

from firefly.widgets.simple import *
from firefly.widgets.combo import *


class ChannelDisplay(QLabel):
    pass


class ToolBarStretcher(QWidget):
    def __init__(self, parent):
        super(ToolBarStretcher, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


class ActionButton(QPushButton):
    pass


class FireflyNotImplementedEditor(QLabel):
    def __init__(self, parent, **kwargs):
        super(FireflyNotImplementedEditor, self).__init__(parent)
        self.val = None

    def set_value(self, value):
        self.setText(str(value))
        self.val = value
        self.default = value

    def get_value(self):
        return self.val

    def setReadOnly(self, *args, **kwargs):
        pass







#TODO

class FireflyRegions(FireflyNotImplementedEditor):
    pass

class FireflyFraction(FireflyNotImplementedEditor):
    pass


meta_editors = {
    STRING    : FireflyString,
    TEXT      : FireflyText,
    INTEGER   : FireflyInteger,
    NUMERIC   : FireflyNumeric,
    BOOLEAN   : FireflyBoolean,
    DATETIME  : FireflyDatetime,
    TIMECODE  : FireflyTimecode,
    REGIONS   : FireflyRegions,
    FRACTION  : FireflyFraction,
    SELECT    : FireflySelect,
    LIST      : FireflyList,
    COLOR     : FireflyColorPicker,
    "radio"   : FireflyRadio
}


class MetaEditor(QWidget):
    def __init__(self, parent, keys):
        super(MetaEditor, self).__init__(parent)
        self.inputs = {}
        self.defaults = {}

        layout = QFormLayout()

        i = 0
        for key, conf in keys:
            key_label = meta_types[key].alias(config.get("language","en"))
            key_description = meta_types[key].description(config.get("language", "en")) or key_label
            key_class = meta_types[key]["class"]
            key_settings = copy.copy(meta_types[key].settings)
            key_settings.update(conf)

            if key_settings.get("mode") == "radio" or key_settings.get("widget") == "radio":
                widget = "radio"
            else:
                widget = key_settings.get("widget", key_class)

            self.inputs[key] = meta_editors.get(
                    widget,
                    FireflyNotImplementedEditor
                )(self, **key_settings)

            self.inputs[key].meta_key = key

            layout.addRow(key_label, self.inputs[key])
            layout.labelForField(self.inputs[key]).setToolTip("<p>{}</p>".format(key_description))
            i+=1
        self.setLayout(layout)

    def keys(self):
        return self.inputs.keys()

    @property
    def meta(self):
        return {key : self[key] for key in self.keys()}

    def __getitem__(self, key):
        return self.inputs[key].get_value()

    def __setitem__(self, key, value):
        self.inputs[key].set_value(value)

    def setEnabled(self, stat):
        for w in self.inputs:
            self.inputs[w].setReadOnly(not stat)

    @property
    def changed(self):
        keys = []
        for key in self.keys():
            if self[key] != self.defaults.get(key, None):
                keys.append(key)
        return keys

    def set_defaults(self):
        self.defaults = {}
        for key in self.keys():
            self.defaults[key] = self[key]
