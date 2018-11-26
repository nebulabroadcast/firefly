import time
import functools

from nx import *

from nebulacore.meta_format import format_select

from .common import *
from .dialogs.text_editor import TextEditorDialog


class ChannelDisplay(QLabel):
    pass

class ToolBarStretcher(QWidget):
    def __init__(self, parent):
        super(ToolBarStretcher, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

class ActionButton(QPushButton):
    pass

#
# Metadata editor widgets
#

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


class FireflyString(QLineEdit):
    def __init__(self, parent, **kwargs):
        super(FireflyString, self).__init__(parent)
        self.default = self.get_value()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setText(str(value))
        self.default = self.get_value()

    def get_value(self):
        return self.text()


class FireflyText(QTextEdit):
    def __init__(self, parent, **kwargs):
        super(FireflyText, self).__init__(parent)
        fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixed_font.setStyleHint(QFont.Monospace);
        self.setCurrentFont(fixed_font)
        self.setTabChangesFocus(True)
        self.default = self.get_value()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setText(str(value))
        self.default = self.get_value()

    def get_value(self):
        return self.toPlainText()


class FireflyInteger(QSpinBox):
    def __init__(self, parent, **kwargs):
        super(FireflyInteger,self).__init__(parent)
        self.setMinimum(kwargs.get("min", 0))
        self.setMaximum(kwargs.get("max", 99999))
        #TODO: set step to 1. disallow floats
        self.default = self.get_value()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setValue(int(value))
        self.default = self.get_value()

    def get_value(self):
        return int(self.value())


class FireflyNumeric(QSpinBox):
    def __init__(self, parent, **kwargs):
        super(FireflyInteger,self).__init__(parent)
        self.setMinimum(kwargs.get("min", -99999))
        self.setMaximum(kwargs.get("max", 99999))
        #TODO: custom step (default 1, allow floats)
        self.default = self.get_value()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setValue(int(value))
        self.default = self.get_value()

    def get_value(self):
        return self.value()


class FireflyDatetime(QLineEdit):
    def __init__(self, parent, **kwargs):
        super(FireflyDatetime,self).__init__(parent)
        mode = kwargs.get("mode", "datetime")

        if mode == "date":
            self.mask   = "9999-99-99"
            self.format = "%Y-%m-%d"

        elif mode == "datetime":
            self.mask   = "9999-99-99 99:99"
            self.format = "%Y-%m-%d %H:%M"

            if kwargs.get("show_seconds", False):
                self.mask += ":99"
                self.format += ":%S"

        self.setInputMask(self.mask)
        self.default = self.get_value()

    def set_value(self, timestamp):
        self.setInputMask("")
        if timestamp:
            tt = time.localtime(timestamp)
            self.setText(time.strftime(self.format, tt))
        else:
            self.setText(self.format.replace("9","-"))
        self.setInputMask(self.mask)
        self.default = self.get_value()

    def get_value(self):
        if not self.text().replace("-", "").replace(":","").strip():
            return float(0)
        t = time.strptime(self.text(), self.format)
        return float(time.mktime(t))


class FireflyTimecode(QLineEdit):
    def __init__(self, parent, **kwargs):
        super(FireflyTimecode,self).__init__(parent)
        self.fps = kwargs.get("fps", 25.0)
        self.setInputMask("99:99:99:99")
        self.setText("00:00:00:00")
        self.default = self.get_value()

        fm = self.fontMetrics()
        w = fm.boundingRect(self.text()).width() + 16
        self.setMinimumWidth(w)
        self.setMaximumWidth(w)

    def set_value(self, value):
        self.setText(s2tc(value, self.fps))
        self.setCursorPosition(0)
        self.default = self.get_value()

    def get_value(self):
        hh, mm, ss, ff = [int(i) for i in self.text().split(":")]
        return (hh*3600) + (mm*60) + ss + (ff/self.fps)




class FireflySelect(QComboBox):
    def __init__(self, parent, **kwargs):
        super(FireflySelect, self).__init__(parent)
        self.cdata = []
        if kwargs.get("data", []):
            self.set_data(kwargs["data"])
        self.default = self.get_value()

    def setReadOnly(self, val):
        self.setEnabled(not val)

    def auto_data(self, key):
        data = [[k["value"], k["alias"], k["selected"]] for k in format_select(key, -1, full=True)]
        self.set_data(data)

    def set_data(self, data):
        self.clear()
        for i, row in enumerate(sorted(data)):
            if len(row) == 3:
                value, label, selected = row
            else:
                value, label = row
                selected = i==0
            if not label:
                label = value
            self.cdata.append(value)
            self.addItem(label)
            if selected:
                self.setCurrentIndex(i)

    def set_value(self, value):
        if value == self.get_value():
            return
        if not value and self.cdata and self.cdata[0] == "0":
            self.setCurrentIndex(0)
            return
        for i, val in enumerate(self.cdata):
            if val == value:
                self.setCurrentIndex(i)
                break
        else:
            self.setCurrentIndex(-1)
        self.default = self.get_value()

    def get_value(self):
        if self.currentIndex() == -1:
            return ""
        return self.cdata[self.currentIndex()]


class FireflyRadio(QWidget):
    def __init__(self, parent, **kwargs):
        super(FireflyRadio, self).__init__(parent)
        self.cdata = []
        self.current_index = -1
        self.buttons = []
        self.set_data(data)
        self.default = self.get_value()

    def set_data(self, data):
        self.current_index = -1
        vbox = QHBoxLayout()
        for i, row in enumerate(sorted(data)):
            value, label = row
            if not label:
                label = value
            self.cdata.append(value)

            self.buttons.append(QPushButton(label))
            self.buttons[-1].setCheckable(True)
            self.buttons[-1].setAutoExclusive(True)
            self.buttons[-1].clicked.connect(partial(self.switch, i))
            vbox.addWidget(self.buttons[-1])

        vbox.setContentsMargins(0,0,0,0)
        self.setLayout(vbox)

    def switch(self, index):
        self.current_index = index

    def set_value(self, value):
        if value == self.get_value():
            return
        for i, val in enumerate(self.cdata):
            if val == value:
                self.buttons[i].setChecked(True)
                self.current_index = i
                break
        else:
            self.current_index = -1
            for button in self.buttons:
                button.setAutoExclusive(False);
                button.setChecked(False);
                button.setAutoExclusive(True);
        self.default = self.get_value()

    def get_value(self):
        if self.current_index == -1:
            return ""
        return self.cdata[self.current_index]

    def setReadOnly(self, val):
        for w in self.buttons:
            w.setEnabled(not val)


class FireflyBoolean(QCheckBox):
    def __init__(self, parent, **kwargs):
        super(FireflyBoolean, self).__init__(parent)
        self.default = self.get_value()

    def setReadOnly(self, val):
        self.setEnabled(not val)

    def set_value(self, value):
        self.setChecked(bool(value))

    def get_value(self):
        return self.isChecked()

#TODO

class FireflyRegions(FireflyNotImplementedEditor):
    pass

class FireflyFraction(FireflyNotImplementedEditor):
    pass

class FireflyList(FireflyNotImplementedEditor):
    pass

class FireflyColorPicker(QPushButton):
    def __init__(self, parent, **kwargs):
        super(FireflyColorPicker, self).__init__(parent)
        self.color = 0
        self.clicked.connect(self.execute)

    def execute(self):
        color = int(QColorDialog.getColor(QColor(self.color)).rgb())
        self.set_value(color)

    def get_value(self):
        return self.color

    def set_value(self, value):
        self.color = value
        self.setStyleSheet("background-color: #{:06x}".format(self.color))

    def setReadOnly(self, stat):
        self.setEnabled(not stat)



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
}


class MetaEditor(QWidget):
    def __init__(self, parent, keys):
        super(MetaEditor, self).__init__(parent)
        self.inputs = {}
        self.defaults = {}

        layout = QFormLayout()

        for key, conf in keys:
            key_label = meta_types[key].alias(config.get("language","en"))
            key_class = meta_types[key]["class"]
            key_settings = meta_types[key].settings
            key_settings.update(conf)

            self.inputs[key] = meta_editors.get(
                    key_class,
                    FireflyNotImplementedEditor
                )(self, **key_settings)

            layout.addRow(key_label, self.inputs[key])
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
        #super(MetaEditor, self).setEnabled(stat)
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
