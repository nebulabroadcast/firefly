import functools

import firefly

from firefly.metadata import meta_types

from firefly.qt import (
    Qt,
    QMenu,
    QAction,
    QWidget,
    QLabel,
    QPushButton,
    QSizePolicy,
    QGridLayout,
)

from .simple import (
    FireflyString,
    FireflyText,
    FireflyInteger,
    FireflyNumeric,
    FireflyBoolean,
    FireflyDatetime,
    FireflyTimecode,
    FireflyColorPicker,
)

from .combo import (
    FireflySelect,
    FireflyList,
    FireflyRadio,
)


class ChannelDisplay(QLabel):
    pass


class ToolBarStretcher(QWidget):
    def __init__(self, parent):
        super(ToolBarStretcher, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


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

    def set_options(self, *args, **kwargs):
        pass

    def get_value(self):
        return self.val

    def setReadOnly(self, *args, **kwargs):
        pass


# TODO
class FireflyRegions(FireflyNotImplementedEditor):
    pass


class FireflyFraction(FireflyNotImplementedEditor):
    pass


meta_editors = {
    "string": FireflyString,
    "text": FireflyText,
    "integer": FireflyInteger,
    "numeric": FireflyNumeric,
    "boolean": FireflyBoolean,
    "datetime": FireflyDatetime,
    "timecode": FireflyTimecode,
    "object": FireflyRegions,
    "fraction": FireflyFraction,
    "select": FireflySelect,
    # "list": FireflyList,
    "color": FireflyColorPicker,
    "radio": FireflyRadio,
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
        layout.setColumnMinimumWidth(0, 150)

        i = 0
        for field in keys:
            key_label = meta_types[field.name].title
            key_description = meta_types[field.name].description or key_label
            key_class = meta_types[field.name].type

            key_settings = meta_types[field.name].dict()
            key_settings.update(field.dict(exclude_none=True, exclude_unset=True))

            if key_settings.get("mode") == "radio":
                widget = "radio"
            else:
                widget = key_settings.get("widget", key_class)

            self.inputs[field.name] = meta_editors.get(
                widget,
                FireflyNotImplementedEditor,
            )(self, **key_settings)

            label = QLabel(key_label, self)
            label.setStyleSheet("padding-top:9px;")

            label.setToolTip(f"<p>{key_description}</p>")
            if parent.__class__.__name__ == "DetailTabMain":
                label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                label.customContextMenuRequested.connect(
                    functools.partial(self.key_menu, field.name)
                )

            self.inputs[field.name].meta_key = field.name
            self.labels[field.name] = label

            layout.addWidget(self.labels[field.name], i, 0, Qt.AlignmentFlag.AlignTop)
            layout.addWidget(self.inputs[field.name], i, 1)

            i += 1

        self.setLayout(layout)
        self.set_defaults()

    def key_menu(self, key, position):
        menu = QMenu()
        section = QAction("Search in...")
        section.setEnabled(False)
        menu.addAction(section)
        for view in firefly.settings.views:
            if view.separator:
                menu.addSeparator()
            action = QAction(view.name, self)
            action.triggered.connect(
                functools.partial(self._parent.search_by_key, key, view.id)
            )
            menu.addAction(action)
        menu.exec(self.labels[key].mapFromGlobal(position))

    def keys(self):
        return self.inputs.keys()

    @property
    def meta(self):
        return {key: self[key] for key in self.keys()}

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
