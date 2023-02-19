from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
)

from firefly.api import api
from firefly.components.input_timecode import InputTimecode
from firefly.log import log


class SplitItemDialog(QDialog):
    def __init__(self, parent, item, head_items, tail_items, id_channel):
        super().__init__(parent)

        self.setWindowTitle(f"Split {item}")
        self.item = item
        self.head_items = head_items
        self.tail_items = tail_items
        self.id_channel = id_channel

        if self.item["id_asset"]:
            self.original_duration = self.item.asset["duration"]
        else:
            self.original_duration = 0

        # Set up the UI elements
        layout = QVBoxLayout()

        # Label for the input field
        label = QLabel("Enter timecodes (HH:MM:SS:FF):")
        layout.addWidget(label)

        # Input field for new timecodes
        input_layout = QHBoxLayout()
        self.input_field = InputTimecode(self)
        input_layout.addWidget(self.input_field)

        # Add button to add a new timecode to the list
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_timecode)
        input_layout.addWidget(add_button)

        layout.addLayout(input_layout)

        # List of existing timecodes
        self.timecode_list = QListWidget()
        self.values = []
        layout.addWidget(self.timecode_list)

        # Button to remove selected timecode from the list
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_timecode)
        layout.addWidget(remove_button)

        # Button to close the dialog
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.split_item)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_timecode(self):
        """Add the timecode from the input field to the list"""
        timecode = self.input_field.text()
        value = self.input_field.get_value()
        if not value:
            return
        if value > self.original_duration:
            return

        self.timecode_list.addItem(timecode)
        self.values.append(value)
        self.input_field.clear()

    def remove_timecode(self):
        """Remove the selected timecode from the list"""
        current_row = self.timecode_list.currentRow()
        if current_row >= 0:
            self.timecode_list.takeItem(current_row)
            self.values.pop(current_row)

    def get_timecodes(self):
        """Return the list of timecodes entered by the user"""
        timecodes = []
        for i in range(self.timecode_list.count()):
            timecodes.append(self.timecode_list.item(i).data(Qt.UserRole))
        return timecodes

    def split_item(self):
        regions = []
        for i, v in enumerate(self.values):
            if i == 0:
                regions.append((0, v))
            else:
                regions.append((self.values[i - 1], v))
        regions.append((self.values[-1], self.original_duration))

        new_order = []  # True faith. he he he
        i = 0
        for item in self.head_items:
            new_order.append({"type": "item", "id": item.id})
            i += 1

        for j, region in enumerate(regions):
            new_order.append(
                {
                    "type": "item",
                    "meta": {
                        "id": self.item.id if j == 0 else None,
                        "mark_in": region[0],
                        "mark_out": region[1],
                        "id_asset": self.item["id_asset"],
                    },
                }
            )
            i += 1

        for item in self.tail_items:
            new_order.append({"type": "item", "id": item.id})
            i += 1

        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        response = api.order(
            id_channel=self.id_channel,
            id_bin=self.item["id_bin"],
            order=new_order,
        )
        QApplication.restoreOverrideCursor()
        if not response:
            log.error(response.message)
        self.accept()


def show_split_dialog(parent, item, head_items, tail_items, id_channel):
    dlg = SplitItemDialog(parent, item, head_items, tail_items, id_channel)
    dlg.exec()
