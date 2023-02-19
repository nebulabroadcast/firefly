import firefly
from firefly.api import api
from firefly.enum import MetaClass
from firefly.log import log
from firefly.metadata import meta_types
from firefly.qt import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QMessageBox,
    QScrollArea,
    Qt,
    QVBoxLayout,
)
from firefly.components.form import MetadataForm

ERR = "** ERROR **"


class BatchOpsDialog(QDialog):
    def __init__(self, parent, objects):
        super(BatchOpsDialog, self).__init__(parent)
        self.objects = sorted(objects, key=lambda obj: obj.id)
        self.setWindowTitle(f"Batch modify: {len(self.objects)} assets")
        id_folder = self.objects[0]["id_folder"]
        self.fields = firefly.settings.get_folder(id_folder)
        self.form = MetadataForm(self, self.fields)

        if self.form:
            for key, conf in self.fields:
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
        self.scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        self.scroll_area.setWidget(self.form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
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
                    " - {}".format(meta_types[k].alias) for k in self.form.changed
                )
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            pass
        else:
            log.info("Save aborted")
            return

        response = api.set(
            objects=[a.id for a in self.objects],
            data={k: self.form[k] for k in self.form.changed},
        )

        if not response:
            log.error(response.message)

        self.response = True
        self.close()


def show_batch_ops_dialog(parent=None, objects=None):
    if objects:
        dlg = BatchOpsDialog(parent, objects)
        dlg.exec()
        return dlg.response
