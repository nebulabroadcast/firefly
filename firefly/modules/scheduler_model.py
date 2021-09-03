import datetime
import functools

from firefly import *
from firefly.modules.scheduler_utils import *
from firefly.dialogs.event import *

__all__ = ["SchedulerCalendar"]


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
        self.day_start = [6, 0] #default

    def drawWidget(self, qp):
        qp.setPen(Qt.NoPen)
        qp.setBrush(COLOR_CALENDAR_BACKGROUND)
        qp.drawRect(0, 0, self.width(), self.height())

        qp.setPen(TIME_PENS[0][1])
        font = QFont('Sans Serif', 9, QFont.Light)
        qp.setFont(font)

        for i in range(0, MINS_PER_DAY, self.resolution):
            if i % 60:
                continue
            y = i * self.min_size
            tc = (self.day_start[0]*60 + self.day_start[1]) + i
            qp.drawLine(0, y, self.width(), y)
            qp.drawText(5, y+15, s2time(tc*60, False, False))



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
        return ts*self.sec_size

    def is_ts_today(self, ts):
        return ts >= self.start_time and ts < self.start_time + SECS_PER_DAY

    def round_ts(self, ts):
        base = 300
        return int(base * round(float(ts)/base))

    def set_time(self, start_time):
        self.start_time = start_time
        self.update()

    def drawWidget(self, qp):
        qp.setPen(Qt.NoPen)
        qp.setBrush(COLOR_DAY_BACKGROUND)
        qp.drawRect(0, 0, self.width(), self.height())

        for i in range(0, MINS_PER_DAY, self.resolution):
            for pen in TIME_PENS:
                if i % pen[0] == 0:
                    qp.setPen(pen[1])
                    break
            else:
                continue
            y = i * self.min_size
            qp.drawLine(0, y, self.width(), y)

        for i,event in enumerate(self.calendar.events):
            if not self.is_ts_today(event["start"]):
                continue
            try:
                end = self.calendar.events[i+1]["start"]
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
        if type(self.calendar.dragging) == Event and self.calendar.dragging.id == event.id:
            if not self.drag_outside:
                return

        TEXT_SIZE = 9
        base_t = self.ts2pos(event["start"])
        base_h = self.min_size * (event["duration"] / 60)
        evt_h = self.ts2pos(end) - base_t

        if event["color"]:
            bcolor = QColor(event["color"])
        else:
            bcolor = QColor(40,80,120)
        bcolor.setAlpha(210)

        # Event block (Gradient one)
        erect = QRect(0,base_t,self.width(),evt_h) # EventRectangle Muhehe!
        gradient = QLinearGradient(erect.topLeft(), erect.bottomLeft())
        gradient.setColorAt(.0, bcolor)
        gradient.setColorAt(1, QColor(0,0,0, 0))
        qp.fillRect(erect, gradient)


        lcolor = QColor("#909090")
        erect = QRect(0, base_t, self.width(), 2)
        qp.fillRect(erect, lcolor)
        if base_h:
            if base_h > evt_h + (SAFE_OVERRUN * self.min_size):
                lcolor = QColor("#e01010")
            erect = QRect(0, base_t, 2, min(base_h, evt_h))
            qp.fillRect(erect, lcolor)


        qp.setPen(QColor("#e0e0e0"))
        font = QFont("Sans", TEXT_SIZE)
        if evt_h > TEXT_SIZE + 15:
            text = text_shorten(event["title"], font, self.width()-10)
            qp.drawText(6, base_t + TEXT_SIZE + 9, text)


    def draw_dragging(self, qp):
        if type(self.calendar.dragging) == Asset:
            exp_dur = suggested_duration(self.calendar.dragging.duration)
        elif type(self.calendar.dragging) == Event:
            exp_dur = self.calendar.dragging["duration"]
        else:
            return

        drop_ts = self.round_ts(self.cursor_time - self.calendar.drag_offset)

        base_t = self.ts2pos(drop_ts)
        base_h = self.sec_size * max(300, exp_dur)

        qp.setPen(Qt.NoPen)
        qp.setBrush(QColor(200,200,200,128))
        qp.drawRect(0, base_t, self.width(), base_h)


        e_start_time = time.strftime("%H:%M", time.localtime(drop_ts)),
        e_end_time = time.strftime("%H:%M", time.localtime(drop_ts + max(300, exp_dur)))
        logging.debug(f"Start time: {e_start_time} End time: {e_end_time}")


    def mouseMoveEvent(self, e):
        mx = e.x()
        my = e.y()
        ts = (my/self.min_size*60) + self.start_time
        for i, event in enumerate(self.calendar.events):
            try:
                end = self.calendar.events[i+1]["start"]
            except IndexError:
                end = self.start_time + SECS_PER_DAY

            if end >= ts > event["start"] >= self.start_time:
                self.cursor_event = event
                diff = event["start"] + event["duration"] - end
                if diff < 0:
                    diff = "Remaining: " + s2tc(abs(diff))
                else:
                    diff = "Over: " + s2tc(diff)

                self.setToolTip(f"<b>{event['title']}</b><br>Start: {format_time(event['start'], '%H:%M')}<br>{diff}")
                break
            self.cursor_event = False
        else:
            self.cursor_event = False


        if not self.cursor_event:
            self.setToolTip("No event scheduled")
            return

        if e.buttons() != Qt.LeftButton:
            return

        self.calendar.drag_offset = ts - event["start"]
        if self.calendar.drag_offset > event["duration"]:
            self.calendar.drag_offset = event["duration"]

        encodedData = json.dumps([event.meta])
        mimeData = QMimeData()
        mimeData.setData("application/nx.event", encodedData.encode("ascii"))

        drag = QDrag(self)
        drag.targetChanged.connect(self.dragTargetChanged)
        drag.setMimeData(mimeData)
        drag.setHotSpot(e.pos() - self.rect().topLeft())
        self.calendar.drag_source = self
        dropAction = drag.exec_(Qt.MoveAction)


    def dragTargetChanged(self, evt):
        if not user.has_right("scheduler_edit", self.calendar.id_channel):
            return
        if type(evt) == SchedulerDayWidget:
            self.drag_outside = False
        else:
            self.drag_outside = True
            self.calendar.drag_source.update()

    def dragEnterEvent(self, evt):
        if not user.has_right("scheduler_edit", self.calendar.id_channel):
            return
        if evt.mimeData().hasFormat('application/nx.asset'):
            d = evt.mimeData().data("application/nx.asset").data()
            d = json.loads(d.decode("ascii"))
            if len(d) != 1:
                evt.ignore()
                return
            asset = Asset(meta=d[0])

            if not eval(self.calendar.playout_config["scheduler_accepts"]):
                evt.ignore()
                return

            self.calendar.dragging = asset
            self.calendar.drag_offset = 20/self.sec_size   #### TODO: SOMETHING MORE CLEVER
            evt.accept()

        elif evt.mimeData().hasFormat('application/nx.event'):
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
        if not user.has_right("scheduler_edit", self.calendar.id_channel):
            return
        self.dragging = True
        self.calendar.focus_data = []
        self.mx = evt.pos().x()
        self.my = evt.pos().y()
        cursor_time = (self.my / self.min_size*60) + self.start_time
        if self.round_ts(cursor_time) != self.round_ts(self.cursor_time):
            self.cursor_time = cursor_time
            self.update()

        # disallow droping event over another event
        if type(self.calendar.dragging) == Event:
            if self.round_ts(self.cursor_time - self.calendar.drag_offset) in [event["start"] for event in self.calendar.events]:
                evt.ignore()
                return
        evt.accept()

    def dragLeaveEvent(self, evt):
        self.dragging = False
        self.update()

    def dropEvent(self, evt):
        drop_ts = max(self.start_time, self.round_ts(self.cursor_time - self.calendar.drag_offset))
        do_reload = False

        if not user.has_right("scheduler_edit", self.id_channel):
            logging.error("You are not allowed to modify schedule of this channel.")
            self.calendar.drag_source = False
            self.calendar.dragging = False
            return


        elif type(self.calendar.dragging) == Asset:

            for event in self.calendar.events:
                if event["start"] == drop_ts:
                    if event["duration"]:
                        ret = QMessageBox.question(self,
                            "Overwrite",
                            f"Do you really want to overwrite a non-empty event?\n{event}",
                            QMessageBox.Yes | QMessageBox.No
                            )
                        if ret == QMessageBox.Yes:
                            pass
                        else:
                            self.calendar.drag_source = False
                            self.calendar.dragging = False
                            self.update()
                            return


            if evt.keyboardModifiers() & Qt.AltModifier:
                logging.info(f"Creating event from {self.calendar.dragging} at time {format_time(self.cursor_time)}")
                if event_dialog(
                        asset=self.calendar.dragging,
                        id_channel=self.id_channel,
                        start=drop_ts
                        ):
                    do_reload = True
            else:
                self.calendar.setCursor(Qt.WaitCursor)
                response = api.schedule(
                        id_channel=self.id_channel,
                        start_time=self.calendar.week_start_time,
                        end_time=self.calendar.week_end_time,
                        events=[{
                                "id_asset" : self.calendar.dragging.id,
                                "start" : drop_ts,
                                "id_channel" : self.id_channel
                            }]

                    )
                self.calendar.setCursor(Qt.ArrowCursor)
                if not response:
                    logging.error(response.message)

            do_reload = True


        elif type(self.calendar.dragging) == Event:
            event = self.calendar.dragging
            move = True

            if event.id and abs(event["start"] - drop_ts) > 7200:
                ret = QMessageBox.question(self,
                    "Move event",
                    f"Do you really want to move {self.cursor_event}?\n\nFrom: {format_time(event['start'])}\nTo: {format_time(drop_ts)}",
                    QMessageBox.Yes | QMessageBox.No
                    )
                if ret == QMessageBox.Yes:
                    move = True
                else:
                    move = False

            if move:
                event["start"] = drop_ts
                if not event.id:
                    logging.debug("Creating empty event")
                    # Create empty event. Event edit dialog is enforced.
                    if event_dialog(
                            id_channel=self.id_channel,
                            start=drop_ts
                        ):
                        do_reload = True
                else:
                    # Just dragging events around. Instant save
                    self.calendar.setCursor(Qt.ArrowCursor)
                    response = api.schedule(
                                id_channel=self.id_channel,
                                start_time=self.calendar.week_start_time,
                                end_time=self.calendar.week_end_time,
                                events=[event.meta]
                            )
                    self.calendar.setCursor(Qt.ArrowCursor)
                    if not response:
                        logging.error(response.message)
                    else:
                        do_reload = response.data

        self.calendar.drag_source = False
        self.calendar.dragging = False
        if type(do_reload) == list:
            self.calendar.set_data(do_reload)
        elif do_reload:
            self.calendar.load()


    def contextMenuEvent(self, event):
        if not self.cursor_event:
            return

        menu = QMenu(self.parent())
        menu.setStyleSheet(app_skin)

        self.calendar.selected_event = self.cursor_event

        action_open_rundown = QAction('Open rundown', self)
        action_open_rundown.triggered.connect(self.on_open_rundown)
        menu.addAction(action_open_rundown)

        action_edit_event = QAction('Event details', self)
        action_edit_event.triggered.connect(self.on_edit_event)
        menu.addAction(action_edit_event)

        if user.has_right("scheduler_edit", self.calendar.id_channel):
            menu.addSeparator()
            action_delete_event = QAction('Delete event', self)
            action_delete_event.triggered.connect(self.on_delete_event)
            menu.addAction(action_delete_event)

        menu.exec_(event.globalPos())

    def mouseDoubleClickEvent(self, evt):
        self.on_open_rundown()

    def on_open_rundown(self):
        self.calendar.open_rundown(self.start_time, self.cursor_event)

    def on_edit_event(self):
        if not self.calendar.selected_event:
            return
        if event_dialog(event=self.calendar.selected_event):
            self.calendar.load()

    def on_delete_event(self):
        if not self.calendar.selected_event:
            return
        cursor_event = self.calendar.selected_event
        if not user.has_right("scheduler_edit", self.id_channel):
            logging.error("You are not allowed to modify schedule of this channel.")
            return

        ret = QMessageBox.question(self,
            "Delete event",
            f"Do you really want to delete {cursor_event}?\nThis operation cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
            )
        if ret == QMessageBox.Yes:
            QApplication.processEvents()
            self.calendar.setCursor(Qt.WaitCursor)
            response = api.schedule(
                    id_channel=self.id_channel,
                    start_time=self.calendar.week_start_time,
                    end_time=self.calendar.week_end_time,
                    delete=[cursor_event.id]
                )
            self.calendar.setCursor(Qt.ArrowCursor)
            if response:
                logging.info(f"{cursor_event} deleted")
                self.calendar.set_data(response.data)
            else:
                logging.error(response.message)
                self.calendar.load()


    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_step = 500

            p = event.angleDelta().y()

            if p > 0:
                if self.last_wheel_direction == -1:
                    self.last_wheel_direction = 0
                else:
                    self.calendar.zoom.setValue(min(10000, self.calendar.zoom.value()+zoom_step))
                    self.last_wheel_direction = 1

            elif p < 0:
                if self.last_wheel_direction == 1:
                    self.last_wheel_direction = 0
                else:
                    self.calendar.zoom.setValue(max(0, self.calendar.zoom.value()-zoom_step))
                    self.last_wheel_direction = -1

        else:
            super(SchedulerDayWidget, self).wheelEvent(event)



class SchedulerDayHeaderWidget(QLabel):
    def __init__(self, parent, dow):
        super(SchedulerDayHeaderWidget, self).__init__(parent)
        self.setStyleSheet("""
                background-color:#161616;
                text-align:center;
                qproperty-alignment: AlignCenter;
                font-size:14px;
                min-height:24px"""
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
            self.setText(f"<font color='red'>{t}</font>")
        elif start_time > time.time():
            self.setText(f"<font color='green'>{t}</font>")
        else:
            self.setText(t)

    def mouseDoubleClickEvent(self, event):
        self.on_open_rundown()

    def contextMenuEvent(self, event):
        menu = QMenu(self.parent())
        menu.setStyleSheet(app_skin)

        action_open_rundown = QAction('Open rundown', self)
        action_open_rundown.triggered.connect(self.on_open_rundown)
        menu.addAction(action_open_rundown)

        action_import_template = QAction("Import template", self)
        action_import_template.triggered.connect(functools.partial(self.parent().parent().import_template, self.dow))
        menu.addAction(action_import_template)

        menu.exec_(event.globalPos())

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
        self.scroll_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)


        zoomlevel = self.parent().app_state.get("scheduler_zoom", 0)
        self.zoom = QSlider(Qt.Horizontal)
        self.zoom.setMinimum(0)
        self.zoom.setMaximum(10000)
        self.zoom.valueChanged.connect(self.on_zoom)
        logging.debug("Setting scheduler zoom level to", zoomlevel)
        self.zoom.setValue(zoomlevel)

        layout = QVBoxLayout()
        layout.addLayout(header_layout)
        layout.addWidget(self.scroll_area,1)
        layout.addWidget(self.zoom,0)
        self.setLayout(layout)
        self.setMinimumHeight(450)


    @property
    def id_channel(self):
        return self.parent().id_channel

    @property
    def playout_config(self):
        return self.parent().playout_config

    @property
    def day_start(self):
        return self.playout_config["day_start"]

    @property
    def event_ids(self):
        return [event.id for event in self.events]

    def load(self, ts=False):
        if not self.week_start_time and not ts:
            ts = time.time()

        if ts:
            dt = datetime.datetime.fromtimestamp(ts)
            week_start = dt - datetime.timedelta(days = dt.weekday())
            week_start = week_start.replace(
                    hour=self.day_start[0],
                    minute=self.day_start[1],
                    second=0
                )
            self.week_start_time = time.mktime(week_start.timetuple())
            self.week_end_time = self.week_start_time + SECS_PER_WEEK

        QApplication.processEvents()
        self.setCursor(Qt.WaitCursor)

        response = api.schedule(
                id_channel=self.id_channel,
                start_time=self.week_start_time,
                end_time=self.week_end_time
            )

        if response:
            self.clock_bar.day_start = self.day_start
            self.clock_bar.update()
            self.set_data(response.data)

            for i, widgets in enumerate(zip(self.days, self.headers)):
                day_widget, header_widget = widgets
                start_time = self.week_start_time + (i * SECS_PER_DAY)
                day_widget.set_time(start_time)
                header_widget.set_time(start_time)
        else:
            logging.error(response.message)
        self.setCursor(Qt.ArrowCursor)
        self.on_zoom()


    def set_data(self, data):
        self.events = []
        for meta in data:
            self.events.append(Event(meta=meta))
        QApplication.processEvents()
        self.update()


    def update(self):
        for day_widget in self.days:
            day_widget.update()
        super(SchedulerCalendar, self).update()

    def open_rundown(self, start_time, event=False):
        self.parent().open_rundown(start_time, event)

    def on_zoom(self):
        ratio = max(1, self.zoom.value() / 1000.0)
        h = self.scroll_area.height() * ratio
        pos = self.scroll_area.verticalScrollBar().value() / self.scroll_widget.height()
        self.scroll_widget.setMinimumHeight(h)
        self.scroll_area.verticalScrollBar().setValue(pos * h)
        self.parent().app_state["scheduler_zoom"] = self.zoom.value()

    def resizeEvent(self, evt):
        self.zoom.setMinimum(self.scroll_area.height())
