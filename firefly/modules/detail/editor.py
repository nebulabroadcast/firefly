from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFrame, QScrollArea, QVBoxLayout, QWidget

import firefly
from firefly.components.form import MetadataForm
from firefly.metadata import meta_types


class AssetEditor(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.fields = []
        self.widgets = {}
        self.layout = QVBoxLayout()
        self.form = False
        self.id_folder = False
        self.status = -1
        self.has_focus = False

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        mwidget = QWidget()
        mwidget.setLayout(self.layout)
        self.scroll_area.setWidget(mwidget)

        scroll_layout = QVBoxLayout()
        scroll_layout.addWidget(self.scroll_area)
        self.setLayout(scroll_layout)

    def load(self, asset, **kwargs):
        id_folder = kwargs.get("id_folder", asset["id_folder"])
        if id_folder != self.id_folder or kwargs.get("force"):
            if not id_folder:
                self.fields = []
            else:
                self.fields = firefly.settings.get_folder(id_folder).fields

            if self.form:
                # SRSLY. I've no idea what I'm doing here
                self.layout.removeWidget(self.form)
                self.form.deleteLater()
                QApplication.processEvents()
                self.form.destroy()
                QApplication.processEvents()
                self.form = None
            for i in reversed(range(self.layout.count())):
                self.layout.itemAt(i).widget().deleteLater()

            self.form = MetadataForm(self, self.fields, {})
            self.layout.addWidget(self.form)
            self.id_folder = id_folder
            self.status = asset["status"]

        if self.form:
            for field in self.fields:
                # if meta_types[field.name].type in ["select", "list"]:
                #     self.form.inputs[field.name].set_field_options(**field.dict())
                self.form[field.name] = asset[field.name]
            self.form.set_defaults()

        if self.form:
            enabled = firefly.user.can("asset_edit", id_folder)
            self.form.setEnabled(enabled)

    def on_focus(self):
        pass

    def search_by_key(self, key, id_view=False):
        b = self.parent().parent().parent().main_window.browser
        id_view = id_view or b.tabs.widget(b.tabs.currentIndex()).id_view
        view_title = firefly.settings.get_view(id_view).title
        asset = self.parent().parent().parent().asset
        b.new_tab(
            f"{view_title}: {asset.show(key)} ({meta_types[key].title})",
            id_view=id_view,
            conds=[f"'{key}' = '{self.form[key]}'"],
        )
        b.redraw_tabs()
