import pprint
import functools

import firefly

from firefly.enum import Colors
from firefly.metadata import meta_types
from firefly.qt import (
    Qt,
    QColor,
    QAbstractTableModel,
    QAbstractItemView,
    QSortFilterProxyModel,
    QTableView,
    pixlib,
    fontlib,
)


@functools.lru_cache(maxsize=100)
def format_header(key):
    if key in meta_types:
        return meta_types[key].header
    return key.replace('_', ' ').title()


@functools.lru_cache(maxsize=100)
def format_description(key):
    if key in meta_types:
        return meta_types[key].description
    return ""


class FireflyViewModel(QAbstractTableModel):
    def __init__(self, parent):
        super(FireflyViewModel, self).__init__(parent)
        self.object_data = []
        self.header_data = []
        self.changed_objects = []

    def rowCount(self, parent):
        return len(self.object_data)

    def columnCount(self, parent):
        return len(self.header_data)

    def headerData(
        self,
        col,
        orientation=Qt.Orientation.Horizontal,
        role=Qt.ItemDataRole.DisplayRole,
    ):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return format_header(self.header_data[col])
            elif role == Qt.ItemDataRole.ToolTipRole:
                desc = format_description(self.header_data[col])
                return f"<p>{desc}</p>" if desc else None
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        obj = self.object_data[row]
        key = self.header_data[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            return obj.format_display(key, model=self)
        elif role == Qt.ItemDataRole.ForegroundRole:
            color = obj.format_foreground(key, model=self)
            return (
                QColor(color.value if isinstance(color, Colors) else color)
                if color
                else None
            )
        elif role == Qt.ItemDataRole.BackgroundRole:
            color = obj.format_background(key, model=self)
            if color is None:
                return None
            return QColor(color.value if isinstance(color, Colors) else color)
        elif role == Qt.ItemDataRole.DecorationRole:
            return pixlib[obj.format_decoration(key, model=self)]
        elif role == Qt.ItemDataRole.FontRole:
            font = obj.format_font(key, model=self)
            return fontlib[font]
        elif role == Qt.ItemDataRole.ToolTipRole:
            if firefly.config.debug:
                r = pprint.pformat(obj.meta)
                if obj.object_type == "item":
                    r += "\n\n" + pprint.pformat(obj.asset.meta) if obj.asset else ""
                return r
            else:
                return obj.format_tooltip(key, model=self)
        return None

    def setData(self, index, data, role=False):
        key = self.header_data[index.column()]
        id_object = self.object_data[index.row()].id
        self.object_data[index.row()][key] = data

        if id_object not in self.changed_objects:
            self.changed_objects.append(id_object)

        self.model.dataChanged.emit(index, index)
        self.update()

        self.refresh()
        return True

    def refresh(self):
        pass


class FireflySortModel(QSortFilterProxyModel):
    def __init__(self, model):
        super(FireflySortModel, self).__init__()
        self.setSourceModel(model)
        self.setDynamicSortFilter(True)
        self.setSortLocaleAware(True)

    @property
    def object_data(self):
        return self.sourceModel().object_data

    def mimeData(self, indexes):
        return self.sourceModel().mimeData([self.mapToSource(idx) for idx in indexes])


class FireflyView(QTableView):
    def __init__(self, parent):
        super(FireflyView, self).__init__(parent)
        self.verticalHeader().setVisible(False)
        self.setWordWrap(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.selected_objects = []
        self.focus_enabled = True

    @property
    def main_window(self):
        return self.parent().main_window
