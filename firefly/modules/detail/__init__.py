import time

from nxtools import format_time
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
)

import firefly
from firefly.api import api
from firefly.base_module import BaseModule
from firefly.enum import ObjectStatus
from firefly.log import log
from firefly.metadata import meta_types
from firefly.modules.detail.editor import AssetEditor
from firefly.modules.detail.preview import AssetPreview
from firefly.modules.detail.toolbars import detail_toolbar
from firefly.objects import Asset, asset_cache


class MetaList(QTextEdit):
    def __init__(self, parent):
        super(MetaList, self).__init__(parent)
        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self.setCurrentFont(fixed_font)
        self.setReadOnly(True)
        self.setStyleSheet("border:0;")
        self.has_focus = False

    def on_focus(self):
        pass


class DetailTabExtended(MetaList):
    def load(self, asset, **kwargs):
        self.tag_groups = {
            "core": [],
            "other": [],
        }
        if not asset["id_folder"]:
            return
        for tag in sorted(meta_types):
            if meta_types[tag].ns in ["a", "i", "e", "b", "o"]:
                self.tag_groups["core"].append(tag)
            elif meta_types[tag].ns in ("f", "q"):
                continue
            elif tag not in [
                r.name for r in firefly.settings.get_folder(asset["id_folder"]).fields
            ]:
                self.tag_groups["other"].append(tag)
        data = ""
        for tag_group in ["core", "other"]:
            for tag in self.tag_groups[tag_group]:
                if tag not in asset.meta:
                    continue
                tag_title = meta_types[tag].title
                value = asset.format_display(tag) or asset[tag] or ""
                if value:
                    data += f"{tag_title:<40}: {value}\n"
            data += "\n\n"
        self.setText(data)


class DetailTabTechnical(MetaList):
    def load(self, asset, **kwargs):
        self.tag_groups = {"File": [], "Format": [], "QC": []}
        for tag in sorted(meta_types):
            if tag.startswith("file") or tag in ["id_storage", "path", "origin"]:
                self.tag_groups["File"].append(tag)
            elif meta_types[tag].ns == "f":
                self.tag_groups["Format"].append(tag)
            elif meta_types[tag].ns == "q" and not tag.startswith("qc/"):
                self.tag_groups["QC"].append(tag)
        data = ""
        if not asset["id_folder"]:
            return
        for tag_group in ["File", "Format", "QC"]:
            for tag in self.tag_groups[tag_group]:
                if tag not in asset.meta:
                    continue
                tag_title = meta_types[tag].title
                value = asset.format_display(tag) or asset["tag"] or ""
                if value:
                    data += f"{tag_title:<40}: {value}\n"
            data += "\n\n"
        self.setText(data)


class DetailTabs(QTabWidget):
    def __init__(self, parent):
        super(DetailTabs, self).__init__()

        self.tab_editor = AssetEditor(self)
        self.tab_extended = DetailTabExtended(self)
        self.tab_technical = DetailTabTechnical(self)
        self.tab_preview = AssetPreview(self)
        self.tabBar().setVisible(False)

        self.addTab(self.tab_editor, "EDITOR")
        self.addTab(self.tab_extended, "EXTENDED")
        self.addTab(self.tab_technical, "TECHNICAL")
        self.addTab(self.tab_preview, "PREVIEW")

        self.currentChanged.connect(self.on_switch)
        self.setCurrentIndex(0)
        self.tabs = [self.tab_editor, self.tab_extended, self.tab_technical]
        self.tabs.append(self.tab_preview)

    def on_switch(self, *args):
        try:
            index = int(args[0])
        except IndexError:
            index = self.currentIndex()

        if index == -1:
            self.tab_preview.player.force_pause()

        for i, tab in enumerate(self.tabs):
            hf = index == i
            tab.has_focus = hf
            if hf:
                tab.on_focus()

    def load(self, asset, **kwargs):
        for tab in self.tabs:
            tab.load(asset, **kwargs)


class DetailModule(BaseModule):
    def __init__(self, parent):
        super(DetailModule, self).__init__(parent)
        self.asset = self._is_loading = self._load_queue = False
        toolbar_layout = QHBoxLayout()

        self.toolbar = detail_toolbar(self)  # , [self.folder_select, self.duration])

        toolbar_layout.addWidget(self.toolbar)
        self.detail_tabs = DetailTabs(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(toolbar_layout, 1)
        layout.addWidget(self.detail_tabs)
        self.setLayout(layout)

    @property
    def form(self):
        return self.detail_tabs.tab_editor.form

    @property
    def preview(self):
        return self.detail_tabs.tab_preview

    def set_title(self, title):
        self.main_window.main_widget.tabs.setTabText(0, title)

    def save_state(self):
        state = {}
        return state

    def load_state(self, state):
        pass

    def switch_tabs(self, idx=-1):
        if idx == -1:
            idx = (self.detail_tabs.currentIndex() + 1) % self.detail_tabs.count()
        self.detail_tabs.setCurrentIndex(idx)

    def check_changed(self):
        changed = []
        if self.form and self.asset:
            if self.asset["id_folder"] != self.folder_select.get_value():
                changed.append("id_folder")
            changed.extend(self.form.changed)
            changed.extend(self.preview.changed)

        if changed:
            reply = QMessageBox.question(
                self,
                "Save changes?",
                f"Following data has been changed in the {self.asset}"
                + "\n\n"
                + "\n".join([meta_types[k].title for k in changed]),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.on_apply()

    def focus(self, asset, silent=False, force=False):
        if not isinstance(asset, Asset):
            return

        log.status(f"[DETAIL] Focusing {asset}")

        if self._is_loading:
            self._load_queue = [asset]
            return
        else:
            self._load_queue = False
            self._is_loading = True

        if not silent:
            self.check_changed()

        #
        # Show data
        #

        self.folder_select.setEnabled(True)

        self.asset = Asset(meta=asset.meta)  # asset deep copy
        self.parent().setWindowTitle(f"Detail of {self.asset}")
        self.detail_tabs.load(self.asset, force=force)
        self.folder_select.set_value(self.asset["id_folder"])

        self.duration.fps = self.asset.fps
        self.duration.set_value(self.asset.duration)
        self.duration.show()
        if (self.asset["status"] == ObjectStatus.OFFLINE) or (not self.asset.id):
            self.duration.setEnabled(True)
        else:
            self.duration.setEnabled(False)

        enabled = (not asset.id) or firefly.user.can(
            "asset_edit", self.asset["id_folder"]
        )
        self.folder_select.setEnabled(enabled)
        self.action_approve.setEnabled(enabled)
        self.action_qc_reset.setEnabled(enabled)
        self.action_reject.setEnabled(enabled)
        self.action_apply.setEnabled(enabled)
        self.action_revert.setEnabled(enabled)

        self.set_title("DETAIL : " + self.asset.__repr__())

        self._is_loading = False
        if self._load_queue:
            self.focus(self._load_queue)

    def on_folder_changed(self, new_folder: int):
        data = {key: self.form[key] for key in self.form.changed}
        self.detail_tabs.load(self.asset, id_folder=new_folder)
        for key in data:
            if key in self.form.inputs:
                self.form[key] = data[key]
            else:
                pass  # TODO: Delete from metadata? How?

    def new_asset(self):
        new_asset = Asset()
        if self.asset and self.asset["id_folder"]:
            new_asset["id_folder"] = self.asset["id_folder"]
        else:
            new_asset["id_folder"] = firefly.settings.folders[0].id
        self.duration.set_value(0)
        self.focus(new_asset)
        self.main_window.show_detail()
        self.detail_tabs.setCurrentIndex(0)

    def clone_asset(self):
        new_asset = Asset()
        if self.asset and self.asset["id_folder"]:
            new_asset["id_folder"] = self.asset["id_folder"]
            for key in self.form.inputs:
                new_asset[key] = self.form[key]
        else:
            new_asset["id_folder"] = firefly.settings.folders[0].id
        new_asset["media_type"] = self.asset["media_type"]
        new_asset["content_type"] = self.asset["content_type"]
        self.asset = False
        self.focus(new_asset)
        self.main_window.show_detail()
        self.detail_tabs.setCurrentIndex(0)

    def on_apply(self):
        if not self.form:
            return
        data = {}

        if self.asset.id:
            if (
                self.asset["id_folder"] != self.folder_select.get_value()
                and self.folder_select.isEnabled()
            ):
                data["id_folder"] = self.folder_select.get_value()
            if (
                self.asset["True"] != self.duration.get_value()
                and self.duration.isEnabled()
            ):
                data["duration"] = self.duration.get_value()

            for key in self.form.changed:
                data[key] = self.form[key]
        else:
            data["id_folder"] = self.folder_select.get_value()
            data["duration"] = self.duration.get_value()
            for key in self.form.changed:
                data[key] = self.form[key]

        if self.preview.changed:
            data.update(self.preview.changed)

        self.setCursor(Qt.CursorShape.BusyCursor)
        response = api.set(id=self.asset.id, data=data)
        if not response:
            log.error(response.message)
        else:
            log.debug("[DETAIL] Set method responded", response.response)
            try:
                aid = response["id"]
            except Exception:
                aid = self.asset.id
            self.asset["id"] = aid
            asset_cache.request([[aid, 0]])

        # self.form.setEnabled(True)

    def on_revert(self):
        if self.asset:
            self.focus(asset_cache[self.asset.id], silent=True)

    def on_set_qc(self, state):
        state_name = {0: "New", 3: "Rejected", 4: "Approved"}[state]
        report = (
            f"{format_time(time.time())} : {firefly.user} "
            f"flagged the asset as {state_name}"
        )

        if self.asset["qc/report"]:
            report = self.asset["qc/report"] + "\n" + report

        response = api.set(
            id=self.asset.id, data={"qc/state": state, "qc/report": report}
        )
        if not response:
            log.error(response.message)
            return
        try:
            aid = response["id"]
        except Exception:
            aid = self.asset.id
        asset_cache.request([[aid, 0]])

    def seismic_handler(self, data):
        pass

    def refresh_assets(self, *objects):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        try:
            current_id = self.asset.id
        except AttributeError:
            return
        if current_id in objects:
            self.focus(asset_cache[self.asset.id], silent=True)
