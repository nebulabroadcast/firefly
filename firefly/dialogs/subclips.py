from firefly import *

class SubclipsModel(QAbstractTableModel):
    def __init__(self, parent, subclips):
        super(SubclipsModel, self).__init__(parent)
        self.parent = parent
        self.header_data = ["Title", "In", "Out"]
        self.array_data  = []
        for k in sorted(subclips, key=lambda k: float(subclips[k][0])):
            self.array_data.append((k, float(subclips[k][0]), float(subclips[k][1])))

    def rowCount(self,parent):
        return len(self.array_data)

    def columnCount(self,parent):
        return len(self.header_data)

    def data(self, index, role):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return self.array_data[row][col]
            elif col in (1,2):
                return s2tc(float(self.array_data[row][col]), base=self.parent.fps)
        return None

    def flags(self, index):
        flags = super(SubclipsModel, self).flags(index)
        if index.isValid():
            flags |= Qt.ItemIsSelectable
        return flags

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header_data[col]
        return None

    @property
    def subclips(self):
        result = {}
        for k, s, e in self.array_data:
            result[k] = [s, e]
        return result


#    def set_data(self):
#        self.beginResetModel()
#        data = json.loads(self.parent.parent.meta.get("Subclips","{}"))
#        self.arraydata = []
#        for r in data.keys():
#            self.arraydata.append((r,data[r][0],data[r][1]))
#        self.endResetModel()



class SubclipsView(QTableView):
    def __init__(self, parent, asset):
        super(SubclipsView, self).__init__()
        self.asset = asset

        vh = self.verticalHeader()
        hh = self.horizontalHeader()

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(self.ExtendedSelection)
        self.setShowGrid(False)

        self.activated.connect(self.on_activated)

        self.model = SubclipsModel(self, self.asset["subclips"] or {})
        self.setModel(self.model)

    @property
    def subclips(self):
        return self.model.subclips

    @property
    def fps(self):
        return fract2float(self.asset["video/fps"] or "25/1")

    def on_activated(self, mi):
        row = mi.row()
        self.parent().selection = self.model.array_data[row][1:]
        self.parent().close()



class SubclipsDialog(QDialog):
    def __init__(self,  parent, asset):
        super(SubclipsDialog, self).__init__(parent)
        self.setWindowTitle("Subclips")
        self.selection = False

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        self.view = SubclipsView(self, asset)

        layout.addWidget(self.view, 1)
        #layout.addWidget(self.form, 2)

        self.setLayout(layout)
        self.setModal(True)
        self.resize(400, 300)
