import firefly

from firefly.qt import QWidget


class BaseModule(QWidget):
    def __init__(self, parent):
        super(BaseModule, self).__init__(parent)
        self.main_window = self.parent().parent()
        self._playout_config = None
        self._id_channel = None

    @property
    def app_state(self):
        return self.main_window.app_state

    @property
    def id_channel(self):
        return self.main_window.id_channel

    @id_channel.setter
    def id_channel(self, value):
        self.main_window.id_channel = int(value)

    @property
    def playout_config(self):
        if self._id_channel != self.id_channel:
            self._playout_config = firefly.settings.get_playout_channel(self.id_channel)
            self._id_channel = self.id_channel
        return self._playout_config

    def seismic_handler(self, message):
        pass
