import os

from nxtools import log_traceback, logging
from PySide6.QtCore import (
    QAbstractTableModel,
    QDate,
    QEvent,
    QItemSelection,
    QItemSelectionModel,
    QMimeData,
    QModelIndex,
    QRect,
    QSettings,
    QSortFilterProxyModel,
    QThread,
    QTimer,
    QUrl,
    QUrlQuery,
)
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QDrag,
    QFont,
    QFontDatabase,
    QFontMetrics,
    QIcon,
    QLinearGradient,
    QPainter,
    QPalette,
    QPen,
    QPixmap,
    Qt,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplashScreen,
    QSplitter,
    QStyle,
    QStyleOptionComboBox,
    QStyleOptionMenuItem,
    QStylePainter,
    QTableView,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import firefly

app_dir = os.getcwd()


class AppSettings:
    def __init__(self):
        self.data = {"name": "qtapp"}

    def get(self, key, default=False):
        return self.data.get(key, default)

    def update(self, data):
        return self.data.update(data)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        if key == "title":
            return self.get(key, self.data["name"])
        return self.data[key]


app_settings = AppSettings()
logging.name = app_settings["name"]


def get_app_state(path):
    return QSettings(path, QSettings.Format.IniFormat)


#
# Skin
#

app_skin = ""
skin_path = os.path.join(app_dir, "skin.css")
if os.path.exists(skin_path):
    try:
        app_skin = open(skin_path).read()
    except Exception:
        log_traceback("Unable to read stylesheet")


class FontLib:
    def __init__(self):
        self.data = {}

    def load(self):

        font_italic = QFont()
        font_italic.setItalic(True)

        font_bold = QFont()
        font_bold.setBold(True)

        font_bolditalic = QFont()
        font_bolditalic.setBold(True)
        font_bolditalic.setItalic(True)

        font_boldunderline = QFont()
        font_boldunderline.setBold(True)
        font_boldunderline.setUnderline(True)

        font_underline = QFont()
        font_underline.setUnderline(True)

        font_strikeout = QFont()
        font_strikeout.setStrikeOut(True)

        self.data = {
            "bold": font_bold,
            "italic": font_italic,
            "bolditalic": font_bolditalic,
            "underline": font_underline,
            "boldunderline": font_boldunderline,
            "strikeout": font_strikeout,
        }

    def __getitem__(self, key):
        if not self.data:
            self.load()
        return self.data.get(key)


def get_pix(name):
    if not name:
        return None
    if name.startswith("folder_"):
        id_folder = int(name.lstrip("folder_"))
        icn = QPixmap(12, 12)
        try:
            color = firefly.settings.get_folder(id_folder).color
        except KeyError:
            color = 0xAAAAAA
        icn.fill(QColor(color))
        return icn
    pixmap = QPixmap(f":/images/{name}.png")
    if not pixmap.width():
        pix_file = os.path.join(app_dir, "images", f"{name}.png")
        if os.path.exists(pix_file):
            return QPixmap(pix_file)
    return None


class PixLib(dict):
    def __call__(self, key):
        return self[key]

    def __getitem__(self, key):
        if key not in self:
            self[key] = get_pix(key)
        return self.get(key, None)


fontlib = FontLib()
pixlib = PixLib()
