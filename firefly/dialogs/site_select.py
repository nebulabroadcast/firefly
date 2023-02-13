import functools

from firefly.config import config
from firefly.qt import QVBoxLayout, QDialog, QIcon, app_skin
from firefly.widgets import ActionButton


class SiteSelectDialog(QDialog):
    def __init__(self, parent):
        super(SiteSelectDialog, self).__init__(parent)
        self.setWindowTitle("Multiple sites are cofigured")
        self.setStyleSheet(app_skin)
        self.setModal(True)
        self.setWindowIcon(QIcon(":/images/firefly.ico"))

        layout = QVBoxLayout()
        for i, site in enumerate(config.sites):
            btn_site = ActionButton(site.title or site.name)
            btn_site.clicked.connect(functools.partial(self.on_select, i))
            layout.addWidget(btn_site, 1)

            self.setLayout(layout)
            self.setMinimumWidth(400)

    def on_select(self, id_site):
        self.close()
        self.setResult(id_site)


def show_site_select_dialog(parent=None):
    """
    Executes a simple dialog with selection of available sites.
    Returns an index of the selected site configuration.
    """
    dlg = SiteSelectDialog(parent)
    return dlg.exec()
