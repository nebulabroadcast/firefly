import functools
import json
import time

from nxtools import datestr2ts, format_time, s2tc, s2time
from PySide6.QtCore import QMimeData, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QDrag, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

import firefly
from firefly.api import api
from firefly.dialogs.event import show_event_dialog
from firefly.helpers.scheduling import can_append
from firefly.log import log
from firefly.objects import Asset, Event
from firefly.qt import app_skin

from .utils import suggested_duration, text_shorten

SECS_PER_DAY = 3600 * 24
MINS_PER_DAY = 60 * 24
SECS_PER_WEEK = SECS_PER_DAY * 7
SAFE_OVERRUN = 5  # Do not warn if overrun < 5 mins
CLOCKBAR_WIDTH = 45
COLOR_CALENDAR_BACKGROUND = QColor("#1f1e26")
COLOR_DAY_BACKGROUND = QColor("#302c3a")

TIME_PENS = [
    (60, QPen(QColor("#ababab"), 2, Qt.PenStyle.SolidLine)),
    (15, QPen(QColor("#999999"), 1, Qt.PenStyle.SolidLine)),
    (5, QPen(QColor("#403035"), 1, Qt.PenStyle.SolidLine)),
]

RUN_PENS = [
    QPen(QColor("#dddd00"), 2, Qt.PenStyle.SolidLine),
    QPen(QColor("#dd0000"), 2, Qt.PenStyle.SolidLine),
]


class SchedulerVerticalBar(QWidget):
    def __init__(self, parent):
        super(SchedulerVerticalBar, self).__init__(parent)
        self.calendar = parent
        self.setMouseTracking(True)

    @property
    def resolution(self):
        if self.min_size > 2:
            return 5
        elif self.min_size > 1:
            return 15
        else:
            return 60

    @property
    def min_size(self):
        return self.height() / MINS_PER_DAY

    @property
    def sec_size(self):
        return self.min_size / 60

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):
        pass


class SchedulerClockBar(SchedulerVerticalBar):
    def __init__(self, parent):
        super(SchedulerClockBar, self).__init__(parent)
        self.setMinimumWidth(CLOCKBAR_WIDTH)
        self.setMaximumWidth(CLOCKBAR_WIDTH)
        self.day_start = [6, 0]  # default

    def drawWidget(self, qp):
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(COLOR_CALENDAR_BACKGROUND)
        qp.drawRect(0, 0, self.width(), self.height())

        qp.setPen(TIME_PENS[0][1])
        font = QFont("Sans Serif", 9, QFont.Weight.Light)
        qp.setFont(font)

        for i in range(0, MINS_PER_DAY, self.resolution):
            if i % 60:
                continue
            y = int(i * self.min_size)
            tc = (self.day_start[0] * 60 + self.day_start[1]) + i
            qp.drawLine(0, y, self.width(), y)
            qp.drawText(5, y + 15, s2time(tc * 60, False, False))


class SchedulerDayWidget(SchedulerVerticalBar):
    def __init__(self, parent):
        super(SchedulerDayWidget, self).__init__(parent)
        self.setMinimumWidth(100)
        self.start_time = 0
        self.setAcceptDrops(True)
        self.cursor_time = 0
        self.cursor_event = False
        self.dragging = False
        self.drag_outside = False
        self.last_wheel_direction = 0

    @property
    def id_channel(self):
        return self.calendar.id_channel

    def ts2pos(self, ts):
        ts -= self.start_time
        return int(ts * self.sec_size)

    def is_ts_today(self, ts):
        return ts >= self.start_time and ts < self.start_time + SECS_PER_DAY

    def round_ts(self, ts):
        base = 300
        return int(base * round(float(ts) / base))

    def set_time(self, start_time):
        self.start_time = start_time
        self.update()

    def drawWidget(self, qp):
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(COLOR_DAY_BACKGROUND)
        qp.drawRect(0, 0, self.width(), self.height())

        for i in range(0, MINS_PER_DAY, self.resolution):
            for pen in TIME_PENS:
                if i % pen[0] == 0:
                    qp.setPen(pen[1])
                    break
            else:
                continue
            y = int(i * self.min_size)
            qp.drawLine(0, y, self.width(), y)

        for i, event in enumerate(self.calendar.events):
            if not self.is_ts_today(event["start"]):
                continue
            try:
                end = self.calendar.events[i + 1]["start"]
            except IndexError:
                end = self.start_time + SECS_PER_DAY

            self.drawBlock(qp, event, end=end)

        # Draw runs
        for id_event, id_asset, start, aired in self.calendar.focus_data:
            if self.is_ts_today(start):
                y = self.ts2pos(start)
                qp.setPen(RUN_PENS[aired])
                qp.drawLine(0, y, self.width(), y)

        if self.calendar.dragging and self.dragging:
            self.draw_dragging(qp)

    def drawBlock(self, qp, event, end):
        if (
            type(self.calendar.dragging) == Event
            and self.calendar.dragging.id == event.id
        ):
            if not self.drag_outside:
                return

        TEXT_SIZE = 9
        base_t = self.ts2pos(event["start"])
        base_h = self.min_size * (event.duration / 60)
        evt_h = self.ts2pos(end) - base_t

        if event["color"]:
            bcolor = QColor(event["color"])
        else:
            bcolor = QColor(40, 80, 120)
        bcolor.setAlpha(210)

        # Event block (Gradient one)
        erect = QRect(0, int(base_t), self.width(), int(evt_h))
        gradient = QLinearGradient(
            0,
            erect.topLeft().y(),
            0,
            int(erect.bottomLeft().y()),
        )
        gradient.setColorAt(0.0, bcolor)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        qp.fillRect(erect, gradient)

        lcolor = QColor("#909090")
        erect = QRect(0, int(base_t), self.width(), 2)
        qp.fillRect(erect, lcolor)
        if base_h:
            if base_h > evt_h + (SAFE_OVERRUN * self.min_size):
                lcolor = QColor("#e01010")
            erect = QRect(0, int(base_t), 2, int(min(base_h, evt_h)))
            qp.fillRect(erect, lcolor)

        qp.setPen(QColor("#e0e0e0"))
        font = QFont("Sans", TEXT_SIZE)
        if evt_h > TEXT_SIZE + 15:
            text = text_shorten(event["title"], font, self.width() - 10)
            qp.drawText(6, base_t + TEXT_SIZE + 9, text)

    def draw_dragging(self, qp):
        if type(self.calendar.dragging) == Asset:
            exp_dur = suggested_duration(self.calendar.dragging.duration)
        elif type(self.calendar.dragging) == Event:
            exp_dur = self.calendar.dragging.duration
        else:
            return

        drop_ts = self.round_ts(self.cursor_time - self.calendar.drag_offset)

        base_t = self.ts2pos(drop_ts)
        base_h = self.sec_size * max(300, exp_dur)

        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(200, 200, 200, 128))
        qp.drawRect(0, base_t, self.width(), base_h)

        e_start_time = time.strftime("%H:%M", time.localtime(drop_ts))
        e_end_time = time.strftime("%H:%M", time.localtime(drop_ts + max(300, exp_dur)))
        log.status(f"[SCHEDULER] Start time: {e_start_time} End time: {e_end_time}")

    def mouseMoveEvent(self, e):
        my = e.pos().y()
        ts = (my / self.min_size * 60) + self.start_time
        for i, event in enumerate(self.calendar.events):
            try:
                end = self.calendar.events[i + 1]["start"]
            except IndexError:
                end = self.start_time + SECS_PER_DAY

            if end >= ts > event["start"] >= self.start_time:
                self.cursor_event = event
                diff = event["start"] + event.duration - end
                if diff < 0:
                    diff = "Remaining: " + s2tc(abs(diff))
                else:
                    diff = "Over: " + s2tc(diff)

                self.setToolTip(
                    f"<b>{event['title']}</b>"
                    f"<br>Start: {format_time(event['start'], '%H:%M')}<br>{diff}"
                )
                break
            self.cursor_event = False
        else:
            self.cursor_event = False

        if not self.cursor_event:
            self.setToolTip("No event scheduled")
            return

        if e.buttons() != Qt.MouseButton.LeftButton:
            return

        self.calendar.drag_offset = ts - event["start"]
        if self.calendar.drag_offset > event.duration:
            self.calendar.drag_offset = event.duration

        encodedData = json.dumps([event.meta])
        mimeData = QMimeData()
        mimeData.setData("application/nx.event", encodedData.encode("ascii"))

        drag = QDrag(self)
        drag.targetChanged.connect(self.dragTargetChanged)
        drag.setMimeData(mimeData)
        drag.setHotSpot(e.pos() - self.rect().topLeft())
        self.calendar.drag_source = self
        drag.exec(Qt.DropAction.MoveAction)

    def dragTargetChanged(self, evt):
        if not firefly.user.can("scheduler_edit", self.calendar.id_channel):
            return
        if type(evt) == SchedulerDayWidget:
            self.drag_outside = False
        else:
            self.drag_outside = True
            self.calendar.drag_source.update()

    def dragEnterEvent(self, evt):
        if not firefly.user.can("scheduler_edit", self.calendar.id_channel):
            return
        if evt.mimeData().hasFormat("application/nx.asset"):
            d = evt.mimeData().data("application/nx.asset").data()
            d = json.loads(d.decode("ascii"))
            if len(d) != 1:
                evt.ignore()
                return
            asset = Asset(meta=d[0])

            if not can_append(asset, self.calendar.playout_config.scheduler_accepts):
                evt.ignore()
                return

            self.calendar.dragging = asset
            self.calendar.drag_offset = (
                20 / self.sec_size
            )  # TODO: SOMETHING MORE CLEVER
            evt.accept()

        elif evt.mimeData().hasFormat("application/nx.event"):
            d = evt.mimeData().data("application/nx.event").data()
            d = json.loads(d.decode("ascii"))
            if len(d) != 1:
                evt.ignore()
                return
            event = Event(meta=d[0])
            self.calendar.dragging = event
            evt.accept()

        else:
            evt.ignore()

        if self.calendar.drag_source:
            self.calendar.drag_source.drag_outside = False
            self.calendar.drag_source.update()

    def dragMoveEvent(self, evt):
        if not firefly.user.can("scheduler_edit", self.calendar.id_channel):
            return
        self.dragging = True
        self.calendar.focus_data = []
        self.mx = evt.pos().x()
        self.my = evt.pos().y()
        cursor_time = (self.my / self.min_size * 60) + self.start_time
        if self.round_ts(cursor_time) != self.round_ts(self.cursor_time):
            self.cursor_time = cursor_time
            self.update()

        # disallow droping event over another event
        if type(self.calendar.dragging) == Event:
            if self.round_ts(self.cursor_time - self.calendar.drag_offset) in [
                event["start"] for event in self.calendar.events
            ]:
                evt.ignore()
                return
        evt.accept()

    def dragLeaveEvent(self, evt):
        self.dragging = False
        self.update()

    def dropEvent(self, evt):
        drop_ts = max(
            self.start_time,
            self.round_ts(self.cursor_time - self.calendar.drag_offset),
        )

        if not firefly.user.can("scheduler_edit", self.id_channel):
            log.error("You are not allowed to modify schedule of this channel.")
            self.calendar.drag_source = False
            self.calendar.dragging = False
            return

        elif type(self.calendar.dragging) == Asset:
            for event in self.calendar.events:
                if event["start"] == drop_ts:
                    if event.duration:
                        ret = QMessageBox.question(
                            self,
                            "Overwrite",
                            f"Do you really want to overwrite {event}",
                            QMessageBox.StandardButton.Yes
                            | QMessageBox.StandardButton.No,
                        )
                        if ret == QMessageBox.StandardButton.Yes:
                            pass
                        else:
                            self.calendar.drag_source = False
                            self.calendar.dragging = False
                            self.update()
                            return

            if evt.keyboardModifiers() & Qt.KeyboardModifier.AltModifier:
                log.info(
                    f"Creating event from {self.calendar.dragging}"
                    f"at time {format_time(self.cursor_time)}"
                )
                if response := show_event_dialog(
                    self,
                    asset=self.calendar.dragging,
                    id_channel=self.id_channel,
                    start=drop_ts,
                    date=self.calendar.date,
                ):
                    self.calendar.set_data(response["events"])
            else:
                self.calendar.setCursor(Qt.CursorShape.WaitCursor)
                if response := api.scheduler(
                    id_channel=self.id_channel,
                    date=self.calendar.date,
                    events=[
                        {
                            "id_asset": self.calendar.dragging.id,
                            "start": drop_ts,
                            "id_channel": self.id_channel,
                        }
                    ],
                ):
                    self.calendar.set_data(response["events"])

        elif type(self.calendar.dragging) == Event:
            event = self.calendar.dragging
            move = True

            if event.id and abs(event["start"] - drop_ts) > 7200:
                ret = QMessageBox.question(
                    self,
                    "Move event",
                    f"Do you really want to move {self.cursor_event}?"
                    f"\n\nFrom: {format_time(event['start'])}"
                    f"\nTo: {format_time(drop_ts)}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if ret == QMessageBox.StandardButton.Yes:
                    move = True
                else:
                    move = False

            if move:
                if not event.id:
                    # Create empty event. Event edit dialog is enforced.
                    self.execute_event_dialog(start=drop_ts)
                else:
                    # Moving existing event around. Instant save
                    if response := api.scheduler(
                        id_channel=self.id_channel,
                        date=self.calendar.date,
                        events=[
                            {
                                "id": event.id,
                                "start": drop_ts,
                            }
                        ],
                    ):
                        self.calendar.set_data(response["events"])
        self.calendar.setCursor(Qt.CursorShape.ArrowCursor)
        self.calendar.drag_source = False
        self.calendar.dragging = False
        self.update()

    def execute_event_dialog(self, **kwargs):
        kwargs["id_channel"] = self.id_channel
        kwargs["date"] = self.calendar.date
        QTimer.singleShot(100, functools.partial(self._execute_event_dialog, kwargs))

    def _execute_event_dialog(self, payload):
        if response := show_event_dialog(self, **payload):
            self.calendar.set_data(response["events"])

    def contextMenuEvent(self, event):
        if not self.cursor_event:
            return

        menu = QMenu(self.parent())
        menu.setStyleSheet(app_skin)

        self.calendar.selected_event = self.cursor_event

        action_open_rundown = QAction("Open rundown", self)
        action_open_rundown.triggered.connect(self.on_open_rundown)
        menu.addAction(action_open_rundown)

        action_edit_event = QAction("Event details", self)
        action_edit_event.triggered.connect(self.on_edit_event)
        menu.addAction(action_edit_event)

        if firefly.user.can("scheduler_edit", self.calendar.id_channel):
            menu.addSeparator()
            action_delete_event = QAction("Delete event", self)
            action_delete_event.triggered.connect(self.on_delete_event)
            menu.addAction(action_delete_event)

        menu.exec(event.globalPos())

    def mouseDoubleClickEvent(self, evt):
        self.on_open_rundown()

    def on_open_rundown(self):
        self.calendar.open_rundown(self.start_time, self.cursor_event)

    def on_edit_event(self):
        if not self.calendar.selected_event:
            return
        if response := show_event_dialog(
            self,
            event=self.calendar.selected_event,
            date=self.calendar.date,
        ):
            self.calendar.set_data(response["events"])

    def on_delete_event(self):
        if not self.calendar.selected_event:
            return
        cursor_event = self.calendar.selected_event
        if not firefly.user.can("scheduler_edit", self.id_channel):
            log.error("You are not allowed to modify schedule of this channel.")
            return

        ret = QMessageBox.question(
            self,
            "Delete event",
            f"Do you really want to delete {cursor_event}?"
            "\nThis operation cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            QApplication.processEvents()
            self.calendar.setCursor(Qt.CursorShape.WaitCursor)
            response = api.scheduler(
                id_channel=self.id_channel,
                delete=[cursor_event.id],
                date=self.calendar.date,
            )
            self.calendar.setCursor(Qt.CursorShape.ArrowCursor)
            if response:
                log.info(f"{cursor_event} deleted")
                self.calendar.set_data(response["events"])
            else:
                log.error(response.message)
                self.calendar.load()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_step = 500

            p = event.angleDelta().y()

            if p > 0:
                if self.last_wheel_direction == -1:
                    self.last_wheel_direction = 0
                else:
                    self.calendar.zoom.setValue(
                        min(10000, self.calendar.zoom.value() + zoom_step)
                    )
                    self.last_wheel_direction = 1

            elif p < 0:
                if self.last_wheel_direction == 1:
                    self.last_wheel_direction = 0
                else:
                    self.calendar.zoom.setValue(
                        max(0, self.calendar.zoom.value() - zoom_step)
                    )
                    self.last_wheel_direction = -1

        else:
            super(SchedulerDayWidget, self).wheelEvent(event)


class SchedulerDayHeaderWidget(QLabel):
    def __init__(self, parent, dow):
        super(SchedulerDayHeaderWidget, self).__init__(parent)
        self.setStyleSheet(
            """
                background-color: #24202e;
                text-align:center;
                qproperty-alignment: AlignCenter;
                font-size:14px;
                padding: 8px;

            """
        )
        self.dow = dow
        self.start_time = 0

    @property
    def id_channel(self):
        return self.parent.id_channel

    def set_time(self, start_time):
        self.start_time = start_time
        t = format_time(start_time, "%a %Y-%m-%d")
        if start_time < time.time() - SECS_PER_DAY:
            self.setText(f"<font color='#ff5f5f'>{t}</font>")
        elif start_time > time.time():
            self.setText(f"<font color='#5fff5f'>{t}</font>")
        else:
            self.setText(t)

    def mouseDoubleClickEvent(self, event):
        self.on_open_rundown()

    def contextMenuEvent(self, event):
        menu = QMenu(self.parent())
        menu.setStyleSheet(app_skin)

        action_open_rundown = QAction("Open rundown", self)
        action_open_rundown.triggered.connect(self.on_open_rundown)
        menu.addAction(action_open_rundown)

        action_import_template = QAction("Import template", self)
        action_import_template.triggered.connect(
            functools.partial(self.parent().parent().import_template, self.dow)
        )
        menu.addAction(action_import_template)

        menu.exec(event.globalPos())

    def on_open_rundown(self):
        self.parent().open_rundown(self.start_time)


class SchedulerCalendar(QWidget):
    def __init__(self, parent):
        super(SchedulerCalendar, self).__init__(parent)
        self.week_start_time = self.week_end_time = 0
        self.events = []
        self.focus_data = []
        self.dragging = False
        self.drag_offset = 0
        self.drag_source = False
        self.append_condition = False
        self.selected_event = False

        header_layout = QHBoxLayout()
        header_layout.addSpacing(CLOCKBAR_WIDTH + 15)

        cols_layout = QHBoxLayout()
        self.clock_bar = SchedulerClockBar(self)
        cols_layout.addWidget(self.clock_bar, 0)

        self.headers = []
        self.days = []
        for i in range(7):
            self.headers.append(SchedulerDayHeaderWidget(self, i))
            self.days.append(SchedulerDayWidget(self))
            header_layout.addWidget(self.headers[-1])
            cols_layout.addWidget(self.days[-1], 1)

        header_layout.addSpacing(20)

        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(cols_layout)
        self.scroll_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        self.zoom = QSlider(Qt.Orientation.Horizontal)
        self.zoom.setMinimum(0)
        self.zoom.setMaximum(10000)
        self.zoom.valueChanged.connect(self.on_zoom)

        layout = QVBoxLayout()
        layout.addLayout(header_layout)
        layout.addWidget(self.scroll_area, 1)
        layout.addWidget(self.zoom, 0)
        self.setLayout(layout)
        self.setMinimumHeight(450)

        QTimer.singleShot(100, self.set_initial_zoom_level)

    def set_initial_zoom_level(self):
        zoomlevel = self.parent().app_state.get("scheduler_zoom", 0)
        log.status("[SCHEDULER] Setting zoom level to", zoomlevel)
        self.zoom.setValue(zoomlevel)

    @property
    def id_channel(self):
        return self.parent().id_channel

    @property
    def playout_config(self):
        return self.parent().playout_config

    @property
    def day_start(self):
        return self.playout_config.day_start

    @property
    def event_ids(self):
        return [event.id for event in self.events]

    @property
    def date(self):
        """Return the first day of week from the parent."""
        return self.parent().date

    def load(self):
        """Load the current week"""
        self.week_start_time = datestr2ts(self.date, *self.day_start)
        self.week_end_time = 3600 * 24 * 7

        QApplication.processEvents()
        self.setCursor(Qt.CursorShape.WaitCursor)

        response = api.scheduler(id_channel=self.id_channel, date=self.date)

        if not response:
            log.error(response.message)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        self.clock_bar.day_start = self.day_start
        self.clock_bar.update()
        self.set_data(response["events"])

        for i, widgets in enumerate(zip(self.days, self.headers)):
            day_widget, header_widget = widgets
            start_time = self.week_start_time + (i * 3600 * 24)
            day_widget.set_time(start_time)
            header_widget.set_time(start_time)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.on_zoom()

    def set_data(self, events: list[dict]):
        self.events = [Event(meta=e) for e in events]
        QApplication.processEvents()
        self.update()

    def update(self):
        for day_widget in self.days:
            day_widget.update()
        super(SchedulerCalendar, self).update()

    def open_rundown(self, start_time, event=False):
        self.parent().open_rundown(start_time, event)

    def on_zoom(self):
        # Calculate the zoom ratio
        ratio = max(1, self.zoom.value() / 1000.0)

        # Calculate the new height of the scroll widget
        h = int(self.scroll_area.height() * ratio)

        # Calculate the current position of the scrollbar relative to the total height
        pos = self.scroll_area.verticalScrollBar().value() / self.scroll_widget.height()

        # Calculate the new position of the scrollbar
        # to center the currently visible area
        new_pos = (
            (pos * self.scroll_widget.height() + 0.5 * self.scroll_area.height()) / h
        ) - (0.5 * self.scroll_area.height() / h)

        # Set the new minimum height of the scroll widget
        # and update the scrollbar position
        self.scroll_widget.setMinimumHeight(h)
        self.scroll_area.verticalScrollBar().setValue(int(new_pos * h))

    def resizeEvent(self, evt):
        self.zoom.setMinimum(self.scroll_area.height())
