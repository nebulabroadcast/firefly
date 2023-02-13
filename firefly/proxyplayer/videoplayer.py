#!/usr/bin/env python3

import functools

from nxtools import logging, log_traceback
from firefly.proxyplayer.utils import get_navbar, RegionBar, TimecodeWindow
from firefly.qt import (
    Qt,
    QWidget,
    QSlider,
    QTimer,
    QHBoxLayout,
    QVBoxLayout,
    QIcon,
)

try:
    from .mpv import MPV

    has_mpv = True
except OSError:
    has_mpv = False
    logging.warning(
        "Unable to load MPV libraries. Video preview will not be available."
    )


class DummyPlayer:
    def property_observer(self, *args):
        return lambda x: x

    def __setitem__(self, key, value):
        return

    def __getitem__(self, key):
        return

    def play(self, *args, **kwargs):
        pass

    def seek(self, *args, **kwargs):
        pass

    def frame_step(self, *args, **kwargs):
        pass

    def frame_back_step(self, *args, **kwargs):
        pass


class VideoPlayer(QWidget):
    def __init__(self, parent=None, pixlib=None):
        super(VideoPlayer, self).__init__(parent)

        self.pixlib = pixlib

        self.markers = {}

        self.video_window = QWidget(self)
        self.video_window.setStyleSheet("background-color: #161616;")
        if not has_mpv:
            self.player = DummyPlayer()
        else:
            try:
                window_id = self.video_window.winId().__int__()
                self.player = MPV(keep_open=True, wid=f"{window_id}")
            except Exception:
                log_traceback(handlers=False)
                self.player = DummyPlayer()

        self.position = 0
        self.duration = 0
        self.mark_in = 0
        self.mark_out = 0
        self.fps = 25.0
        self.loaded = False
        self.duration_changed = False

        self.prev_position = 0
        self.prev_duration = 0
        self.prev_mark_in = 0
        self.prev_mark_out = 0

        #
        # Displays
        #

        self.mark_in_display = TimecodeWindow(self)
        self.mark_in_display.setToolTip("Selection start")
        self.mark_in_display.returnPressed.connect(
            functools.partial(self.on_mark_in, self.mark_in_display)
        )

        self.mark_out_display = TimecodeWindow(self)
        self.mark_out_display.setToolTip("Selection end")
        self.mark_out_display.returnPressed.connect(
            functools.partial(self.on_mark_out, self.mark_out_display)
        )

        self.io_display = TimecodeWindow(self)
        self.io_display.setToolTip("Selection duration")
        self.io_display.setReadOnly(True)

        self.position_display = TimecodeWindow(self)
        self.position_display.setToolTip("Clip position")
        self.position_display.returnPressed.connect(
            functools.partial(self.seek, self.position_display)
        )

        self.duration_display = TimecodeWindow(self)
        self.duration_display.setToolTip("Clip duration")
        self.duration_display.setReadOnly(True)

        #
        # Controls
        #

        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(0, 0)
        self.timeline.sliderMoved.connect(self.on_timeline_seek)
        self.region_bar = RegionBar(self)
        self.navbar = get_navbar(self)

        #
        # Layout
        #

        bottom_bar = QHBoxLayout()
        top_bar = QHBoxLayout()

        top_bar.addWidget(self.mark_in_display, 0)
        top_bar.addStretch(1)
        top_bar.addWidget(self.io_display, 0)
        top_bar.addStretch(1)
        top_bar.addWidget(self.mark_out_display, 0)

        bottom_bar.addWidget(self.position_display, 0)
        bottom_bar.addWidget(self.navbar, 1)
        bottom_bar.addWidget(self.duration_display, 0)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.video_window)
        layout.addWidget(self.region_bar)
        layout.addWidget(self.timeline)
        layout.addLayout(bottom_bar)

        self.setLayout(layout)
        self.navbar.setFocus()

        @self.player.property_observer("time-pos")
        def time_observer(_name, value):
            self.on_time_change(value)

        @self.player.property_observer("duration")
        def duration_observer(_name, value):
            self.on_duration_change(value)

        @self.player.property_observer("pause")
        def pause_observer(_name, value):
            self.on_pause_change(value)

        # Displays updater

        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.on_display_timer)
        self.display_timer.start(40)

    @property
    def frame_dur(self):
        return 1 / self.fps

    def load(self, path, mark_in=0, mark_out=0, markers={}):
        self.loaded = False
        self.markers = markers
        self.player["pause"] = True
        self.player.play(path)
        self.prev_mark_in = -1
        self.prev_mark_out = -1
        self.mark_in = mark_in
        self.mark_out = mark_out
        self.mark_in_display.set_value(0)
        self.mark_out_display.set_value(0)
        self.duration_display.set_value(0)
        self.position_display.set_value(0)

    def on_time_change(self, value):
        self.position = value

    def on_duration_change(self, value):
        if value:
            self.duration = value
            self.loaded = True
        else:
            self.duration = 0
            self.loaded = False
        self.duration_changed = True
        self.region_bar.update()

    def on_pause_change(self, value):
        if hasattr(self, "action_play"):
            self.action_play.setIcon(QIcon(self.pixlib[["pause", "play"][int(value)]]))

    def on_timeline_seek(self):
        if not self.loaded:
            return
        try:
            self.player["pause"] = True
            self.player.seek(self.timeline.value() / 100.0, "absolute", "exact")
        except Exception:
            pass

    def on_frame_next(self):
        if not self.loaded:
            return
        self.player.frame_step()

    def on_frame_prev(self):
        if not self.loaded:
            return
        self.player.frame_back_step()

    def on_5_next(self):
        if not self.loaded:
            return
        self.player.seek(5 * self.frame_dur, "relative", "exact")

    def on_5_prev(self):
        if not self.loaded:
            return
        self.player.seek(-5 * self.frame_dur, "relative", "exact")

    def on_go_start(self):
        if not self.loaded:
            return
        self.player.seek(0, "absolute", "exact")

    def on_go_end(self):
        if not self.loaded:
            return
        self.player.seek(self.duration, "absolute", "exact")

    def on_go_in(self):
        if not self.loaded:
            return
        self.seek(self.mark_in)

    def on_go_out(self):
        if not self.loaded:
            return
        self.seek(self.mark_out or self.duration)

    def on_mark_in(self, value=False):
        if not self.loaded:
            return
        if value:
            if isinstance(value, TimecodeWindow):
                value = value.get_value()
            self.seek(min(max(value, 0), self.duration))
            self.mark_in = value
            self.setFocus()
        else:
            self.mark_in = self.position
        self.region_bar.update()

    def on_mark_out(self, value=False):
        if not self.loaded:
            return
        if value:
            if isinstance(value, TimecodeWindow):
                value = value.get_value()
            self.seek(min(max(value, 0), self.duration))
            self.mark_out = value
            self.setFocus()
        else:
            self.mark_out = self.position
        self.region_bar.update()

    def on_clear_in(self):
        if not self.loaded:
            return
        self.mark_in = 0
        self.region_bar.update()

    def on_clear_out(self):
        if not self.loaded:
            return
        self.mark_out = 0
        self.region_bar.update()

    def on_clear_marks(self):
        if not self.loaded:
            return
        self.mark_out = self.mark_in = 0
        self.region_bar.update()

    def seek(self, position):
        if not self.loaded:
            return
        if isinstance(position, TimecodeWindow):
            position = position.get_value()
            self.setFocus()
        self.player.seek(position, "absolute", "exact")

    def on_pause(self):
        if not self.loaded:
            return
        self.player["pause"] = not self.player["pause"]

    def force_pause(self):
        if not self.loaded:
            return
        if not self.player["pause"]:
            self.player["pause"] = True

    def update_marks(self):
        i = self.mark_in
        o = self.mark_out or self.duration
        self.mark_in_display.set_value(i)
        self.mark_out_display.set_value(o)
        io = o - i + self.frame_dur
        if io > 0:
            self.io_display.set_value(io)
        else:
            self.io_display.set_value(0)
        self.prev_mark_in = self.mark_in
        self.prev_mark_out = self.mark_out

    def on_display_timer(self):
        if not self.loaded:
            return

        if self.position != self.prev_position and self.position is not None:
            self.position_display.set_value(self.position)
            self.timeline.setValue(int(self.position * 100))
            self.prev_position = self.position

        if self.duration != self.prev_duration and self.position is not None:
            self.duration_display.set_value(self.duration)
            self.timeline.setMaximum(int(self.duration * 100))
            self.prev_duration = self.duration

        if (
            self.mark_in != self.prev_mark_in
            or self.mark_out != self.prev_mark_out
            or self.duration_changed
        ):
            self.update_marks()
            self.duration_changed = False
