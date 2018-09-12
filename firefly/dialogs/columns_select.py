from firefly import *

class ColumnsSelectDialog(QDialog):
    def __init__(self,  parent, available=[], current=[]):
        super(ColumnsSelectDialog, self).__init__(parent)
        self.list_available  = QListWidget(self)
        self.list_available.setDragDropMode(QAbstractItemView.DragDrop);
        self.list_current = QListWidget(self)
        self.list_current.setDragDropMode(QAbstractItemView.DragDrop);

        for i in range(5):
            self.list_available.addItem("Item {}".format(i))

        for i in range(5):
            self.list_current.addItem("Item 1{}".format(i))

        list_layout = QHBoxLayout()
        list_layout.addWidget(self.list_available)
        list_layout.addWidget(self.list_current)
        self.setLayout(list_layout)
