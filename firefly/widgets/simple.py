from nx import *
from firefly.common import *


from firefly.dialogs.text_editor import TextEditorDialog



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

    def insertFromMimeData(self,source):
        self.insertPlainText(source.text())


class FireflyInteger(QSpinBox):
    def __init__(self, parent, **kwargs):
        super(FireflyInteger,self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimum(kwargs.get("min", 0))
        self.setMaximum(kwargs.get("max", 99999))
        if kwargs.get("hide_null"):
            logging.info("HIDE NULL")
            self.setMinimum(0)
            self.setSpecialValueText(" ")
        self.setSingleStep(1)
        self.default = self.get_value()

    def wheelEvent(self, event):
        if self.hasFocus():
            super(FireflyInteger, self).wheelEvent(event)
        else:
            event.ignore()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setValue(int(value))
        self.default = self.get_value()

    def get_value(self):
        return int(self.value())


class FireflyNumeric(QSpinBox):
    def __init__(self, parent, **kwargs):
        super(FireflyNumeric,self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimum(kwargs.get("min", -99999))
        self.setMaximum(kwargs.get("max", 99999))
        if kwargs.get("hide_null"):
            logging.info("HIDE NULL")
            self.setMinimum(0)
            self.setSpecialValueText(" ")
        #TODO: custom step (default 1, allow floats)
        self.default = self.get_value()

    def wheelEvent(self, event):
        if self.hasFocus():
            super(FireflyNumeric, self).wheelEvent(event)
        else:
            event.ignore()

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

        elif mode == "year":
            self.mask = "9999"
            self.format = "%Y"

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
