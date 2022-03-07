import os

from nxtools import logging, log_traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *

Signal = pyqtSignal
Slot = pyqtSlot
Property = pyqtProperty

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


def get_app_state(path):
    return QSettings(path, QSettings.IniFormat)


logging.name = app_settings["name"]

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
