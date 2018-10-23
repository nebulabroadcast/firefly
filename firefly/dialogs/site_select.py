import functools

from firefly import *

__all__ = ["site_select_dialog"]

class SiteSelectButton(QPushButton):
    pass

class SiteSelectDialog(QDialog):
    def __init__(self,  parent, sites=[]):
        super(SiteSelectDialog, self).__init__(parent)
        self.setWindowTitle("Multiple sites are cofigured")
        self.setStyleSheet(app_skin)
        self.setModal(True)
        self.sites = sites
        self.setWindowIcon(QIcon(":/images/firefly.ico"))

        layout = QVBoxLayout()
        for i, site in enumerate(sites):
            btn_site = SiteSelectButton(site.get("site_title", False) or site["site_name"])
            btn_site.clicked.connect(functools.partial(self.on_select, i))
            layout.addWidget(btn_site, 1)

            self.setLayout(layout)
            self.setMinimumWidth(400)

    def on_select(self, id_site):
        self.close()
        self.setResult(id_site)


def site_select_dialog():
    """
    Executes a simple dialog with selection of available sites.
    Returns an index of the selected site configuration.
    """
    dlg = SiteSelectDialog(None, config["sites"])
    return dlg.exec_()

