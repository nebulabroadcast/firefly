from nxtools import logging

from firefly.api import api
from firefly.core.common import config
from firefly.core.metadata import meta_types
from firefly.core.enum import MetaClass
from firefly.widgets import MetaEditor
from firefly.qt import (
    Qt,
    QDialog,
    QScrollArea,
    QFrame,
    QDialogButtonBox,
    QVBoxLayout,
    QMessageBox,
)


ERR = "** ERROR **"


class BatchOpsDialog(QDialog):
    def __init__(self, parent, objects):
        super(BatchOpsDialog, self).__init__(parent)
        self.objects = sorted(objects, key=lambda obj: obj.id)
        self.setWindowTitle(f"Batch modify: {len(self.objects)} assets")
        id_folder = self.objects[0]["id_folder"]
        self.keys = config["folders"][id_folder]["meta_set"]
        self.form = MetaEditor(self, self.keys)

        if self.form:
            for key, conf in self.keys:
                if meta_types[key]["class"] in [MetaClass.SELECT, MetaClass.LIST]:
                    self.form.inputs[key].auto_data(
                        meta_types[key], id_folder=id_folder
                    )

                values = []
                for obj in self.objects:
                    val = obj[key]
                    if val not in values:
                        values.append(val)
                if len(values) == 1:
                    self.form[key] = values[0]
            self.form.set_defaults()

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.scroll_area.setWidget(self.form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.on_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area, 2)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.response = False
        self.resize(800, 800)

    def on_cancel(self):
        self.close()

    def on_accept(self):
        reply = QMessageBox.question(
            self,
            "Save changes?",
            "{}".format(
                "\n".join(
                    " - {}".format(meta_types[k].alias(config.get("language", "en")))
                    for k in self.form.changed
                )
            ),
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            pass
        else:
            logging.info("Save aborted")
            return

        response = api.set(
            objects=[a.id for a in self.objects],
            data={k: self.form[k] for k in self.form.changed},
        )

        if not response:
            logging.error(response.message)

        self.response = True
        self.close()


def show_batch_ops_dialog(objects):
    dlg = BatchOpsDialog(None, objects)
    dlg.exec_()
    return dlg.response
