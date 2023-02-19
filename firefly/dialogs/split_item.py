from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
)


from firefly.components.input_timecode import InputTimecode


class SplitItemDialog(QDialog):
    def __init__(self, parent, item, head_items, tail_items, id_channel):
        super().__init__(parent)

        self.setWindowTitle(f"Split {item}")
        self.item = item
        self.head_items = head_items
        self.tail_items = tail_items
        self.id_channel = id_channel

        # Set up the UI elements
        layout = QVBoxLayout()

        # Label for the input field
        label = QLabel("Enter timecodes (HH:MM:SS:FF):")
        layout.addWidget(label)

        # Input field for new timecodes
        input_layout = QHBoxLayout()
        self.input_field = InputTimecode(self)
        # self.input_field.setPlaceholderText("00:00:00:00")
        # self.input_field.setInputMask("99:99:99:99")
        # self.input_field.setValidator(
        #     QRegularExpressionValidator(
        #         r"^[0-9][0-9]:[0-5][0-9]:[0-5][0-9]:[0-9][0-9]$", self
        #     )
        # )
        input_layout.addWidget(self.input_field)

        # Add button to add a new timecode to the list
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_timecode)
        input_layout.addWidget(add_button)

        layout.addLayout(input_layout)

        # List of existing timecodes
        self.timecode_list = QListWidget()
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
        if timecode != "":
            self.timecode_list.addItem(timecode)
            self.input_field.clear()

    def remove_timecode(self):
        """Remove the selected timecode from the list"""
        current_row = self.timecode_list.currentRow()
        if current_row >= 0:
            self.timecode_list.takeItem(current_row)

    def get_timecodes(self):
        """Return the list of timecodes entered by the user"""
        timecodes = []
        for i in range(self.timecode_list.count()):
            timecodes.append(self.timecode_list.item(i).text())
        return timecodes

    def split_item(self):
        self.accept()


def show_split_dialog(parent, item, head_items, tail_items, id_channel):
    dlg = SplitItemDialog(parent, item, head_items, tail_items, id_channel)
    dlg.exec()
