from nxtools import *
from pyqtbs import *
from .version import FIREFLY_VERSION

from nx import *

DEBUG, INFO, WARNING, ERROR, GOOD_NEWS = range(5)

logging.user = ""
logging.handlers = []

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
    pixmap = QPixmap(":/images/{}.png".format(name))
    if not pixmap.width():
        pix_file = os.path.join(app_dir, "images", "{}.png".format(name))
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
