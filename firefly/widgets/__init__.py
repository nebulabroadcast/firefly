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
    def __init__(self, parent, keys, **kwargs):
        super(MetaEditor, self).__init__(parent)
        self.inputs = {}
        self.labels = {}
        self.defaults = {}
        self._parent = parent

        layout = QGridLayout()
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 3)


        i = 0
        for key, conf in keys:
            key_label = meta_types[key].alias()
            key_description = meta_types[key].description() or key_label
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


            label = QLabel(key_label, self)
            label.setStyleSheet("padding-top:9px;")

            label.setToolTip("<p>{}</p>".format(key_description))
            if parent.__class__.__name__ == "DetailTabMain":
                label.setContextMenuPolicy(Qt.CustomContextMenu)
                label.customContextMenuRequested.connect(functools.partial(self.key_menu, key))

            self.inputs[key].meta_key = key
            self.labels[key] = label

            layout.addWidget(self.labels[key], i, 0, Qt.AlignTop)
            layout.addWidget(self.inputs[key], i, 1)


            i+=1

        self.setLayout(layout)


    def key_menu(self, key, position):
        menu = QMenu()
        section = QAction("Search in...")
        section.setEnabled(False)
        menu.addAction(section)
        for id_view in sorted(
                    config["views"].keys(),
                    key=lambda k: config["views"][k]["position"]
                ):
            view = config["views"][id_view]
            if view.get("separator", False):
                menu.addSeparator()
            action = QAction(view["title"], self)
            action.triggered.connect(functools.partial(self._parent.search_by_key, key, id_view))
            menu.addAction(action)
        menu.exec_(self.labels[key].mapToGlobal(position))


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
