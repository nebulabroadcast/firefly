from .common import *

__all__ = ["BaseModule"]

class BaseModule(QWidget):
    def __init__(self, parent):
        super(BaseModule, self).__init__(parent)
        self.main_window = self.parent().parent()

    @property
    def app_state(self):
        return self.main_window.app_state

    @property
    def id_channel(self):
        return self.main_window.id_channel

    @id_channel.setter
    def id_channel(self, value):
        logging.info("Set id_channel to", value)
        self.main_window.id_channel = int(value)

    @property
    def playout_config(self):
        return config["playout_channels"][self.id_channel]

    def seismic_handler(self, message):
        pass
