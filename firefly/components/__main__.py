import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
)

from ffwidgets.input_timecode import InputTimecode


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()

        self.input_timecode1 = InputTimecode(self)
        self.input_timecode2 = InputTimecode(self, value=100, fps=25)

        self.button = QPushButton("Print", self)
        self.button.clicked.connect(self.print)

        layout.addWidget(self.input_timecode1)
        layout.addWidget(self.input_timecode2)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def print(self):
        print(self.input_timecode1.get_value())
        print(self.input_timecode2.get_value())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("My PySide6 Application")
    window.setGeometry(100, 100, 400, 400)

    central_widget = MainWidget()
    window.setCentralWidget(central_widget)
    window.show()
    sys.exit(app.exec())
