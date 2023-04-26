from PySide6.QtWidgets import QVBoxLayout, QWidget

import firefly
from firefly.log import log
from firefly.modules.detail.subclips import FireflySubclipsView
from firefly.modules.detail.toolbars import preview_toolbar
from firefly.proxyplayer import VideoPlayer
from firefly.qt import pixlib


class AssetPreview(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
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
            proxy_url = f"{firefly.config.site.host}/proxy/{self.current_asset.id}"
            log.debug(f"[DETAIL] Opening {self.current_asset} preview: {proxy_url}")
            proxy_url += f"?token={firefly.config.site.token}"
            self.player.fps = self.current_asset.fps
            if self.current_asset["poster_frame"]:
                markers = {
                    "poster_frame": {"position": self.current_asset["poster_frame"]}
                }
            else:
                markers = {}
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
        self.player.markers["poster_frame"] = {"position": self.player.position}
        self.player.region_bar.update()

    def go_to_poster(self):
        pos = self.player.markers.get("poster_frame", {}).get("position", 0)
        if pos:
            self.player.seek(pos)

    def save_marks(self):
        if (
            self.player.mark_in
            and self.player.mark_out
            and self.player.mark_in >= self.player.mark_out
        ):
            log.error("Unable to save marks. In point must precede out point")
        else:
            self.changed["mark_in"] = self.player.mark_in
            self.changed["mark_out"] = self.player.mark_out

    def restore_marks(self):
        pass

    def create_subclip(self):
        if not self.subclips.isVisible():
            self.subclips.show()
        if (
            not (self.player.mark_in and self.player.mark_out)
        ) or self.player.mark_in >= self.player.mark_out:
            log.error("Unable to create subclip. Invalid region selected.")
            return
        self.subclips.create_subclip(self.player.mark_in, self.player.mark_out)

    def manage_subclips(self):
        if self.subclips.isVisible():
            self.subclips.hide()
        else:
            self.subclips.show()
