import functools
import math

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QHBoxLayout, QSlider, QVBoxLayout, QWidget

from firefly.log import log
from firefly.proxyplayer.utils import RegionBar, TimecodeWindow, get_navbar


class VideoPlayer(QWidget):
    def __init__(self, parent=None, pixlib=None):
        super().__init__(parent)

        self.pixlib = pixlib

        self.markers = {}

        self.video_window = QVideoWidget(self)
        self.video_window.setStyleSheet("background-color: #161616;")

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_window)

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

        self.seek_to = None

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top_bar)
        layout.addWidget(self.video_window)
        layout.addWidget(self.region_bar)
        layout.addWidget(self.timeline)
        layout.addLayout(bottom_bar)

        self.setLayout(layout)
        self.navbar.setFocus()

        self.player.playbackStateChanged.connect(self.playback_state_changed)
        self.player.positionChanged.connect(self.on_position_change)
        self.player.durationChanged.connect(self.on_duration_change)
        self.player.errorOccurred.connect(self.on_error)
        self.player.mediaStatusChanged.connect(self.on_media_status)

        # Displays updater

        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.on_display_timer)
        self.display_timer.start(40)

        self.seek_timer = QTimer()
        self.seek_timer.timeout.connect(self.on_seek_timer)
        self.seek_timer.start(100)

    @property
    def frame_dur(self):
        return 1 / self.fps

    def snap(self, position):
        """Round a position (seconds) down to the start of its frame."""
        return math.floor(position * self.fps + 1e-6) / self.fps

    def load(self, path, mark_in=0, mark_out=0, markers=None):
        if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()

        self.loaded = False
        self.markers = markers or {}
        self.position = 0
        self.duration = 0

        self.player.setSource(QUrl(path))
        # pausing (rather than stopping) makes the player show the first frame
        self.player.pause()

        self.prev_mark_in = -1
        self.prev_mark_out = -1
        self.mark_in = mark_in
        self.mark_out = mark_out
        self.mark_in_display.set_value(0)
        self.mark_out_display.set_value(0)
        self.duration_display.set_value(0)
        self.position_display.set_value(0)

    def playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.action_play.setIcon(QIcon(self.pixlib["pause"]))
        else:
            self.action_play.setIcon(QIcon(self.pixlib["play"]))

    def on_media_status(self, status):
        # Like mpv's keep-open: stay paused on the last frame instead of
        # stopping (Qt would restart from the beginning on next play)
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.pause()
            self.seek(self.duration)

    def on_error(self, error, message):
        log.warning(f"Video player: {message}")

    def on_position_change(self, value):
        self.position = self.snap(value / 1000)

    def on_duration_change(self, value):
        if value:
            self.duration = value / 1000
            self.loaded = True
        else:
            self.duration = 0
            self.loaded = False
        self.duration_changed = True
        self.region_bar.update()

    def on_timeline_seek(self):
        if not self.loaded:
            return
        self.force_pause()
        self.seek_to = self.timeline.value() / 100.0

    def on_frame_next(self):
        if not self.loaded:
            return
        self.seek(self.position + self.frame_dur)

    def on_frame_prev(self):
        if not self.loaded:
            return
        self.seek(self.position - self.frame_dur)

    def on_5_next(self):
        if not self.loaded:
            return
        self.seek(self.position + (5 * self.frame_dur))

    def on_5_prev(self):
        if not self.loaded:
            return
        self.seek(self.position - (5 * self.frame_dur))

    def on_go_start(self):
        if not self.loaded:
            return
        self.seek(0)

    def on_go_end(self):
        if not self.loaded:
            return
        self.seek(self.duration - self.frame_dur)

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
        last_frame = max(self.duration - self.frame_dur, 0)
        position = self.snap(min(max(position, 0), last_frame))
        # Update immediately, so repeated frame steps accumulate
        # before the player reports the new position
        self.position = position
        # Aim at the middle of the frame: seeking to its exact start returns
        # the previous frame on proxies that are not intra-only
        self.player.setPosition(round((position + self.frame_dur / 2) * 1000))

    def on_pause(self):
        if not self.loaded:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def force_pause(self):
        if not self.loaded:
            return
        self.player.pause()

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
            if not self.timeline.isSliderDown():
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

    def on_seek_timer(self):
        if self.seek_to is not None:
            self.seek(self.seek_to)
            self.seek_to = None
