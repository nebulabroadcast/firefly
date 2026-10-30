from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
)

import firefly
from firefly.api import api
from firefly.components.form import MetadataForm
from firefly.log import log
from firefly.metadata import meta_types

ERR = "** ERROR **"


class BatchOpsDialog(QDialog):
    def __init__(self, parent, objects):
        super().__init__(parent)
        self.objects = sorted(objects, key=lambda obj: obj.id)
        self.setWindowTitle(f"Batch modify: {len(self.objects)} assets")
        id_folder = self.objects[0]["id_folder"]
        self.fields = firefly.settings.get_folder(id_folder).fields
        self.form = MetadataForm(self, self.fields, {})

        # pre-fill the values all selected assets share
        for field in self.fields:
            values = []
            for obj in self.objects:
                val = obj[field.name]
                if val not in values:
                    values.append(val)
            if len(values) == 1:
                self.form[field.name] = values[0]
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
                "\n".join(f" - {meta_types[k].title}" for k in self.form.changed)
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
    return None
