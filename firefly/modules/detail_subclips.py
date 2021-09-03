import copy

from firefly.common import *
from firefly.widgets import *
from firefly.view import *

__all__ = ["FireflySubclipsView"]

DEFAULT_HEADER_DATA = [
        "mark_in",
        "mark_out",
        "title",
    ]

header_format = {
        "mark_in" : "In",
        "mark_out" : "Out",
        "title" : "Title",
    }

colw = {
        "mark_in" : 120,
        "mark_out" : 120,
        "title" : 300,
    }


class SubclipsModel(FireflyViewModel):
    def __init__(self, *args, **kwargs):
        super(SubclipsModel, self).__init__(*args, **kwargs)
        self.header_data = DEFAULT_HEADER_DATA

    def headerData(self, col, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return header_format[self.header_data[col]]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        obj = self.object_data[row]
        key = self.header_data[index.column()]
        if role == Qt.DisplayRole:
            return meta_types[key].show(obj[key])
        return None

    def load(self, data):
        self.beginResetModel()
        if data:
            self.object_data = data
            self.object_data.sort(key=lambda row: row["mark_in"])
        else:
            self.object_data = []
        self.endResetModel()


class FireflySubclipsView(FireflyView):
    def __init__(self, parent):
        super(FireflySubclipsView, self).__init__(parent)
        self.model = SubclipsModel(self)
        self.setModel(self.model)
        self.activated.connect(self.on_activate)
        for i, h in enumerate(self.model.header_data):
            if h in colw :
                self.horizontalHeader().resizeSection(i, colw[h])
        self.horizontalHeader().setStretchLastSection(True)

    def load(self, data=False):
        if not data:
            if self.parent().current_asset:
                data = copy.deepcopy(self.parent().current_asset["subclips"])
            else:
                data = {}
        self.model.load(data)

    def update_source(self):
        self.parent().changed["subclips"] = self.model.object_data


    def create_subclip(self, mark_in, mark_out):
        fps = self.parent().current_asset["video/fps_f"]
        if mark_in and mark_out and mark_in > mark_out:
            logging.error("Unable to create subclip. In point must precede out point")
            return
        text, ok = QInputDialog.getText(
                self,
                f"Create a subclip",
                f"{s2tc(mark_in, fps)} - {s2tc(mark_out, fps)}\n\nEnter the subclip name:"
            )
        if not ok:
            return
        text = text.strip()
        cdata = self.model.object_data
        cdata.append({
                "mark_in" : mark_in,
                "mark_out" : mark_out,
                "title" : text
            })
        self.load(cdata)
        self.update_source()


    def on_activate(self, mi):
        obj = self.model.object_data[mi.row()]
        self.parent().player.mark_in = obj["mark_in"]
        self.parent().player.mark_out = obj["mark_out"]
        self.parent().player.region_bar.update()
        self.parent().player.seek(obj["mark_in"])


    @property
    def selected_indexes(self):
        result = []
        for idx in self.selectionModel().selectedIndexes():
            i = idx.row()
            if not i in result:
                result.append(i)
        return result

    def contextMenuEvent(self, event):
        if not self.selected_indexes:
            return

        menu = QMenu(self)
        if len(self.selected_indexes) == 1:
            action_update_marks = QAction('Update marks', self)
            action_update_marks.setStatusTip('Update subclip marks using current selection')
            action_update_marks.triggered.connect(self.on_update_marks)
            menu.addAction(action_update_marks)

            action_rename_subclip = QAction('Rename', self)
            action_rename_subclip.setStatusTip('Rename selected subclip')
            action_rename_subclip.triggered.connect(self.on_rename_subclip)
            menu.addAction(action_rename_subclip)

        action_delete_subclip = QAction('Delete', self)
        action_delete_subclip.setStatusTip('Delete selected subclip(s)')
        action_delete_subclip.triggered.connect(self.on_delete_subclip)
        menu.addAction(action_delete_subclip)

        menu.exec_(event.globalPos())


    def on_update_marks(self):
        try:
            idx = self.selected_indexes[0]
        except IndexError:
            return
        mark_in = self.parent().player.mark_in
        mark_out = self.parent().player.mark_out
        if mark_in and mark_out and mark_in > mark_out:
            logging.error("Unable to modify subclip. In point must precede out point")
            return

        self.model.beginResetModel()
        self.model.object_data[idx]["mark_in"] = mark_in
        self.model.object_data[idx]["mark_out"] = mark_out
        self.model.endResetModel()
        self.update_source()



    def on_delete_subclip(self):
        idxs = self.selected_indexes
        if not idxs:
            return
        self.model.beginResetModel()
        idxs.sort(reverse=True)
        for idx in idxs:
            self.model.object_data.pop(idx)
        self.model.endResetModel()
        self.update_source()

    def on_rename_subclip(self):
        try:
            idx = self.selected_indexes[0]
        except IndexError:
            return
        old_name = self.model.object_data[idx]["title"]
        text, ok = QInputDialog.getText(
                self,
                "Rename the subclip",
                f"Original name: {old_name}\n\nEnter the subclip name:"
            )
        if not ok:
            return

        text = text.strip()

        if old_name != text:
            self.model.beginResetModel()
            self.model.object_data[idx]["title"] = text
            self.model.endResetModel()
            self.update_source()
