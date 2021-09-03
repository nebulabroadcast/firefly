from nxtools import *
from pyqtbs import *
from .version import *

from .api import api

from nx import *

DEBUG, INFO, WARNING, ERROR, GOOD_NEWS = range(5)

logging.user = ""
logging.handlers = []

class FontLib():
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
                "bold" : font_bold,
                "italic" : font_italic,
                "bolditalic" : font_bolditalic,
                "underline" : font_underline,
                "boldunderline" : font_boldunderline,
                "strikeout" : font_strikeout
           }

    def __getitem__(self, key):
        if not self.data:
            self.load()
        return self.data.get(key)

fonts = FontLib()


#
# pix library
#

def get_pix(name):
    if not name:
        return None
    if name.startswith("folder_"):
        id_folder = int(name.lstrip("folder_"))
        icn = QPixmap(12, 12)
        try:
            color = config["folders"][id_folder]["color"]
        except KeyError:
            color = 0xaaaaaa
        icn.fill(QColor(color))
        return icn
    pixmap = QPixmap(f":/images/{name}.png")
    if not pixmap.width():
        pix_file = os.path.join(app_dir, "images", f"{name}.png")
        if os.path.exists(pix_file):
            return QPixmap(pix_file)
    return None

class PixLib(dict):
    def __getitem__(self, key):
        if not key in self:
            self[key] = get_pix(key)
        return self.get(key, None)


ABOUT_TEXT = \
    "<b>Firefly - Nebula broadcast automation system client application</b>" \
    "<br><br>" \
    "Named after American space Western drama television series which ran from 2002–2003, " \
    "created by writer and director Joss Whedon" \
    "<br><br>" \
    "Firefly is free software; " \
    "you can redistribute it and/or modify it under the terms of the GNU General Public " \
    "License as published by the Free Software Foundation; " \
    "either version 3 of the License, or (at your option) any later version." \
    "<br><br>" \
    "For more information visit <a href=\"https://nebulabroadcast.com\" style=\"color: #009fbc;\">https://nebulabroadcast.com</a>"

def about_dialog(parent):
    QMessageBox.about(parent, "Firefly {}".format(FIREFLY_VERSION), ABOUT_TEXT)


pix_lib = PixLib()


def has_right(*args, **kwargs):
    return user.has_right(*args, **kwargs)


if PLATFORM == "unix":
    import subprocess

    def notify(text, header, expire):
        subprocess.Popen([
                "notify-send",
                "-t", str(expire),
                header,
                text
            ])

def notify_send(text, level=INFO):
    caption, expire = {
            DEBUG : ["debug", 1],
            INFO : ["info", 3],
            WARNING : ["warning", 5],
            ERROR : ["error", 10],
            GOOD_NEWS : ["good news", 5]
        }[level]
    caption = f"Firefly {caption}"
    if level < WARNING:
        return

    notify(text, caption, expire)
