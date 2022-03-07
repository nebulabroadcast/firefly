import os
import enum

from nxtools import logging, get_guid

from firefly.core.common import config
from firefly.qt import QFont, QPixmap, QColor, app_dir


logging.user = ""
logging.handlers = []

CLIENT_ID = get_guid()


class Colors(enum.Enum):
    TEXT_NORMAL = "#f0f0f0"
    TEXT_FADED = "#a0a0a0"
    TEXT_FADED2 = "#707070"
    TEXT_HIGHLIGHT = "#ffffff"
    TEXT_GREEN = "#15f015"
    TEXT_YELLOW = "#e0f015"
    TEXT_RED = "#f01515"
    TEXT_BLUE = "#1515f0"
    LIVE_BACKGROUND = "#500000"


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
            color = config["folders"][id_folder]["color"]
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
