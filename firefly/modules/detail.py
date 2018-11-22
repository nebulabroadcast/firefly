from firefly import *
from firefly.modules.detail_toolbars import *
from firefly.modules.detail_subclips import *

try:
    from proxyplayer import VideoPlayer
    has_player = True
except OSError:
    log_traceback()
    logging.warning("Unable to load MPV libraries. Video preview will not be available.")
    has_player = False


class DetailTabMain(QWidget):
    def __init__(self, parent):
        super(DetailTabMain, self).__init__(parent)
        self.keys = []
        self.widgets = {}
        self.layout = QVBoxLayout()
        self.form = False
        self.id_folder = False
        self.status = -1
        self.has_focus = False

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setContentsMargins(0,0,0,0)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        mwidget = QWidget()
        mwidget.setLayout(self.layout)
        self.scroll_area.setWidget(mwidget)

        scroll_layout = QVBoxLayout()
        scroll_layout.addWidget(self.scroll_area)
        self.setLayout(scroll_layout)


    def load(self, asset, **kwargs):
        id_folder = kwargs.get("id_folder", asset["id_folder"])
        if id_folder != self.id_folder:
            if not id_folder:
                self.keys = []
            else:
                self.keys = config["folders"][id_folder]["meta_set"]

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

            self.form = MetaEditor(self, self.keys)
            self.layout.addWidget(self.form)
            self.id_folder = id_folder
            self.status = asset["status"]

        if self.form:
            for key, conf in self.keys:
                if meta_types[key]["class"] == SELECT:
                   self.form.inputs[key].set_data([[k["value"], k["alias"]] for k in asset.show(key, full=True)])
                self.form[key] = asset[key]
            self.form.set_defaults()

        if self.form:
            enabled = has_right("asset_edit", id_folder)
            self.form.setEnabled(enabled)

    def on_focus(self):
        pass


class MetaList(QTextEdit):
    def __init__(self, parent):
        super(MetaList, self).__init__(parent)
        fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setCurrentFont(fixed_font)
        self.setReadOnly(True)
        self.setStyleSheet("border:0;")
        self.has_focus = False

    def on_focus(self):
        pass


class DetailTabExtended(MetaList):
    def load(self, asset, **kwargs):
        self.tag_groups = {
                "core" :  [],
                "other"  : [],
            }
        if not asset["id_folder"]:
            return
        for tag in sorted(meta_types):
            if meta_types[tag]["ns"] in ["a", "i", "e", "b", "o"]:
                self.tag_groups["core"].append(tag)
            elif meta_types[tag]["ns"] in ("f", "q"):
                continue
            elif tag not in [r[0] for r in config["folders"][asset["id_folder"]]["meta_set"]]:
                self.tag_groups["other"].append(tag)
        data = ""
        for tag_group in ["core", "other"]:
            for tag in self.tag_groups[tag_group]:
                if not tag in asset.meta:
                    continue
                tag_title = meta_types[tag].alias(config.get("language","en"))
                value = asset.format_display(tag) or asset["tag"] or ""
                if value:
                    data += "{:<40}: {}\n".format(tag_title, value)
            data += "\n\n"
        self.setText(data)


class DetailTabTechnical(MetaList):
    def load(self, asset, **kwargs):
        self.tag_groups = {
                "File" : [],
                "Format"  : [],
                "QC"   : []
            }
        for tag in sorted(meta_types):
            if tag.startswith("file") or tag in ["id_storage", "path", "origin"]:
                self.tag_groups["File"].append(tag)
            elif meta_types[tag]["ns"] == "f":
                self.tag_groups["Format"].append(tag)
            elif meta_types[tag]["ns"] == "q" and not tag.startswith("qc/"):
                self.tag_groups["QC"].append(tag)
        data = ""
        if not asset["id_folder"]:
            return
        for tag_group in ["File", "Format", "QC"]:
            for tag in self.tag_groups[tag_group]:
                if not tag in asset.meta:
                    continue
                tag_title = meta_types[tag].alias(config.get("language","en"))
                value = asset.format_display(tag) or asset["tag"] or ""
                if value:
                    data += "{:<40}: {}\n".format(tag_title, value)
            data += "\n\n"
        self.setText(data)



class DetailTabPreview(QWidget):
    def __init__(self, parent):
        super(DetailTabPreview, self).__init__(parent)
        layout = QVBoxLayout()
        self.player = VideoPlayer(self, pixlib)
        self.subclips = FireflySubclipsView(self)
        toolbar = preview_toolbar(self)

        layout.addWidget(toolbar, 0)
        layout.addWidget(self.player, 3)
        layout.addWidget(self.subclips, 1)
        self.setLayout(layout)
        self.subclips.hide()
        self.has_focus = False
        self.loaded = False
        self.changed = {}

    @property
    def current_asset(self):
        return self.parent().parent().parent().asset

    def load(self, asset, **kwargs):
        self.loaded = False
        self.changed = {}
        if self.has_focus:
            self.load_video()
        self.subclips.load()

    def load_video(self):
        if self.current_asset and not self.loaded:
            logging.debug("Opening {} preview".format(self.current_asset))
            self.player.fps = self.current_asset.fps
            if self.current_asset["poster_frame"]:
                markers = {"poster_frame" : {"position" : self.current_asset["poster_frame"]}}
            else:
                markers = {}
            proxy_url = config["hub"] +  self.current_asset.proxy_url
            logging.debug("Opening", proxy_url)
            self.player.load(
                    proxy_url,
                    mark_in=self.current_asset["mark_in"],
                    mark_out=self.current_asset["mark_out"],
                    markers=markers,
                )
            self.loaded = True

    def on_focus(self):
        self.load_video()

    def set_poster(self):
        self.changed["poster_frame"] = self.player.position
        self.player.markers["poster_frame"] = {"position" : self.player.position}
        self.player.region_bar.update()

    def go_to_poster(self):
        pos = self.player.markers.get("poster_frame",{}).get("position", 0)
        if pos:
            self.player.seek(pos)

    def save_marks(self):
        if self.player.mark_in and self.player.mark_out and self.player.mark_in > self.player.mark_out:
            logging.error("Unable to save marks. In point must precede out point")
        else:
            self.changed["mark_in"] = self.player.mark_in
            self.changed["mark_out"] = self.player.mark_out

    def restore_marks(self):
        pass

    def create_subclip(self):
        if not self.subclips.isVisible():
            self.subclips.show()
        self.subclips.create_subclip(self.player.mark_in, self.player.mark_out)

    def manage_subclips(self):
        if self.subclips.isVisible():
            self.subclips.hide()
        else:
            self.subclips.show()



class DetailTabs(QTabWidget):
    def __init__(self, parent):
        super(DetailTabs, self).__init__()

        self.tab_main = DetailTabMain(self)
        self.tab_extended = DetailTabExtended(self)
        self.tab_technical = DetailTabTechnical(self)
        if has_player:
            self.tab_preview = DetailTabPreview(self)

        self.addTab(self.tab_main, "MAIN")
        self.addTab(self.tab_extended, "EXTENDED")
        self.addTab(self.tab_technical, "TECHNICAL")
        if has_player:
            self.addTab(self.tab_preview, "PREVIEW")

        self.currentChanged.connect(self.on_switch)
        self.setCurrentIndex(0)
        self.tabs = [
                self.tab_main,
                self.tab_extended,
                self.tab_technical
            ]
        if has_player:
            self.tabs.append(self.tab_preview)

    def on_switch(self, *args):
        try:
            index = int(args[0])
        except:
            index = self.currentIndex()

        if index == -1 and has_player:
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
        self.toolbar = detail_toolbar(self)
        self.detail_tabs = DetailTabs(self)
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.detail_tabs)
        self.setLayout(layout)

    @property
    def form(self):
        return self.detail_tabs.tab_main.form

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
            idx = (self.detail_tabs.currentIndex()+1) % self.detail_tabs.count()
        self.detail_tabs.setCurrentIndex(idx)

    def focus(self, asset, silent=False):
        if not isinstance(asset, Asset):
            logging.debug("[DETAIL] Only assets can be focused. Is: {}".format(type(asset)))
            return

        logging.debug("[DETAIL] Focusing", asset)

        if self._is_loading:
            self._load_queue = [asset]
            return
        else:
            self._load_queue = False
            self._is_loading = True

        #
        # Save changes?
        #

        changed = []
        if self.form and self.asset and not silent:
            if self.asset["id_folder"] != self.folder_select.get_value():
                changed.append("id_folder")
            changed.extend(self.form.changed)
            changed.extend(self.preview.changed)

        if changed:
            reply = QMessageBox.question(
                    self,
                    "Save changes?",
                    "Following data has been changed in the {}\n\n{}".format(
                        self.asset, "\n".join(
                            [meta_types[k].alias(config.get("language", "en")) for k in changed]
                        )),
                    QMessageBox.Yes | QMessageBox.No
                    )

            if reply == QMessageBox.Yes:
                self.on_apply()

        #
        # Show data
        #

        self.folder_select.setEnabled(True)

        self.asset = Asset(meta=asset.meta) # asset deep copy
        self.parent().setWindowTitle("Detail of {}".format(self.asset))
        self.detail_tabs.load(self.asset)
        self.folder_select.set_value(self.asset["id_folder"])


        self.duration.fps = self.asset.fps
        self.duration.set_value(self.asset.duration)
        self.duration.show()
        if self.asset["status"] == OFFLINE or not self.asset.id:
            self.duration.setEnabled(True)
        else:
            self.duration.setEnabled(False)


        enabled = (not asset.id) or has_right("asset_edit", self.asset["id_folder"])
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

    def on_folder_changed(self):
        data = {key: self.form[key] for key in self.form.changed}
        self.detail_tabs.load(self.asset, id_folder=self.folder_select.get_value())
        for key in data:
            if key in self.form.inputs:
                self.form[key] = data[key]
            else:
                pass #TODO: Delete from metadata? How?


    def new_asset(self):
        new_asset = Asset()
        if self.asset and self.asset["id_folder"]:
            new_asset["id_folder"] = self.asset["id_folder"]
        else:
            new_asset["id_folder"] = min(config["folders"])
        self.duration.set_value(0)
        self.focus(new_asset)

    def clone_asset(self):
        new_asset = Asset()
        if self.asset and self.asset["id_folder"]:
            new_asset["id_folder"] = self.asset["id_folder"]
            for key in self.form.inputs:
                new_asset[key] = self.form[key]
                new_asset["duration"] = self.duration.get_value()
        else:
            new_asset["id_folder"] = min(config["folders"])
        new_asset["media_type"] = self.asset["media_type"]
        new_asset["content_type"] = self.asset["content_type"]
        self.asset = False
        self.focus(new_asset)

    def on_apply(self):
        if not self.form:
            return
        data = {}

        if self.asset.id:
            if self.asset["id_folder"] != self.folder_select.get_value() and self.folder_select.isEnabled():
                data["id_folder"] = self.folder_select.get_value()
            if self.asset["True"] != self.duration.get_value() and self.duration.isEnabled():
                data["duration"] = self.duration.get_value()

            for key in self.form.changed:
                data[key] = self.form[key]
        else:
            data["id_folder"] = self.folder_select.get_value()
            data["duration"] = self.duration.get_value()
            for key in self.form.keys():
                data[key] = self.form[key]

        if has_player and self.preview.changed:
            data.update(self.preview.changed)

        self.form.setEnabled(False) # reenable on seismic message with new data
        response = api.set(objects=[self.asset.id], data=data)
        if response.is_error:
            logging.error(response.message)
            self.form.setEnabled(True) # reenable on seismic message with new data
        else:
            logging.debug("[DETAIL] Set method responded", response.response)
            if not self.asset.id:
                aid = response.data[0]
                asset_cache.request([[aid, 0]])
                self.focus(asset_cache[aid], silent=True)



    def on_revert(self):
        if self.asset:
            self.focus(asset_cache[self.asset.id], silent=True)

    def on_set_qc(self, state):
        response = api.set(objects=[self.asset.id], data={"qc/state" : state})
        if response.is_error:
            logging.error(response.message)

    def seismic_handler(self, data):
        if data.method == "objects_changed" and data.data["object_type"] == "asset" and self.asset:
            if self.asset.id in data.data["objects"] and self.asset.id:
                self.focus(asset_cache[self.asset.id], silent=True)
