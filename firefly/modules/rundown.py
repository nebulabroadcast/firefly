import time
import datetime
import functools

from firefly import *

from .rundown_utils import *
from .rundown_mcr import MCR
from .rundown_plugins import PlayoutPlugins
from .rundown_view import RundownView


class RundownModule(BaseModule):
    def __init__(self, parent):
        super(RundownModule, self).__init__(parent)
        self.start_time = 0
        self.current_item = False
        self.cued_item = False
        self.last_search = ""
        self.first_load = True

        self.edit_wanted = self.app_state.get("edit_enabled", True)
        self.edit_enabled = False

        self.toolbar = rundown_toolbar(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.toolbar, 0)

        self.view = RundownView(self)

        self.mcr = self.plugins = False

        if user.has_right("mcr", anyval=True):
            self.mcr = MCR(self)
            self.plugins = PlayoutPlugins(self)
            if self.app_state.get("show_mcr", False):
                self.mcr.show()
            else:
                self.mcr.hide()

            if self.app_state.get("show_plugins", False):
                self.plugins.show()
            else:
                self.plugins.hide()
            layout.addWidget(self.mcr)
            layout.addWidget(self.plugins)

        layout.addWidget(self.view, 1)
        self.setLayout(layout)


    def toggle_rundown_edit(self, val=None):
        if val is None:
            self.edit_enabled = not self.edit_enabled
            self.edit_wanted = self.edit_enabled
        else:
            self.edit_enabled = val
            self.edit_wanted = val
        self.app_state["edit_enabled"] = self.edit_wanted
        self.view.setDragEnabled(self.edit_enabled)
        self.main_window.action_rundown_edit.setChecked(self.edit_enabled)



    @property
    def can_edit(self):
        return user.has_right("rundown_edit", self.id_channel)

    @property
    def can_schedule(self):
        return user.has_right("scheduler_edit", self.id_channel)

    def load(self, **kwargs):
        event = kwargs.get("event", False)
        go_to_now = kwargs.get("go_to_now", False)
        # Save current selection
        selection = []
        for idx in self.view.selectionModel().selectedIndexes():
            if self.view.model().object_data[idx.row()].id:
                selection.append([
                        self.view.model().object_data[idx.row()].object_type,
                        self.view.model().object_data[idx.row()].id
                    ])

        do_update_header = kwargs.get("do_update_header", False)
        if "id_channel" in kwargs and kwargs["id_channel"] != self.id_channel:
            do_update_header = True
            self.id_channel = kwargs["id_channel"]

        if "start_time" in kwargs:
            new_start = day_start(kwargs["start_time"], self.playout_config["day_start"])
            if new_start != self.start_time:
                do_update_header = True
                self.start_time = new_start

        if not self.start_time:
            do_update_header = True
            self.start_time = day_start(time.time(), self.playout_config["day_start"])

        self.view.model().load(functools.partial(self.load_callback, do_update_header, selection, event, go_to_now))



    def load_callback(self, do_update_header, selection, event=False, go_to_now=False):
        if do_update_header:
            self.update_header()

        if self.first_load:
            #TODO: Load from appstate
            self.view.horizontalHeader().resizeSection(0, 300)
            self.first_load = False

        if event:
            for i, r in enumerate(self.view.model().object_data):
                if event.id == r.id and r.object_type == "event":
                    self.view.scrollTo(
                            self.view.model().index(i, 0, QModelIndex()),
                            QAbstractItemView.PositionAtTop
                        )
                    break

        # Restore selection
        if selection:
            item_selection = QItemSelection()
            for i, row in enumerate(self.view.model().object_data):
                if [row.object_type, row.id] in selection:
                   i1 = self.view.model().index(i, 0, QModelIndex())
                   i2 = self.view.model().index(i, len(self.view.model().header_data)-1, QModelIndex())
                   item_selection.select(i1,i2)
            self.view.focus_enabled = False
            self.view.selectionModel().select(item_selection, QItemSelectionModel.ClearAndSelect)
        self.view.focus_enabled = True


        if go_to_now:
            for i,r in enumerate(self.view.model().object_data):
                if self.current_item == r.id and r.object_type=="item":
                    self.view.scrollTo(self.view.model().index(i, 0, QModelIndex()), QAbstractItemView.PositionAtTop  )
                    break


    def update_header(self):
        ch = self.playout_config["title"]
        t = datetime.date.fromtimestamp(self.start_time)
        if t < datetime.date.today():
            s = " color='red'"
        elif t > datetime.date.today():
            s = " color='green'"
        else:
            s = ""
        t = t.strftime("%A %Y-%m-%d")
        self.parent().setWindowTitle(f"Rundown {t}")
        self.channel_display.setText(f"<font{s}>{t}</font> - {ch}")
        logging.debug(f"[RUNDOWN] Header update ({ch})")

    #
    # Actions
    #

    def set_channel(self, id_channel):
        if self.id_channel != id_channel:
            self.id_channel = id_channel

    def on_channel_changed(self):
        self.load(do_update_header=True)
        self.plugins.load()

        if self.mcr:
            self.mcr.on_channel_changed()

        can_rundown_edit = has_right("rundown_edit", self.id_channel)
        self.main_window.action_rundown_edit.setEnabled(can_rundown_edit)
        self.toggle_rundown_edit(can_rundown_edit and self.edit_wanted)


    def go_day_prev(self):
        self.load(start_time=self.start_time - (3600*24))

    def go_day_next(self):
        self.load(start_time=self.start_time + (3600*24))

    def go_now(self):
        if not (self.start_time + 86400 > time.time() > self.start_time):
            #do not use day_start here. it will be used in the load method
            self.load(start_time=int(time.time()), go_to_now=True)
        else:
            for i,r in enumerate(self.view.model().object_data):
                if self.current_item == r.id and r.object_type=="item":
                    self.view.scrollTo(self.view.model().index(i, 0, QModelIndex()), QAbstractItemView.PositionAtTop  )
                    break


    def show_calendar(self):
        y, m, d = get_date()
        if not y:
            return
        hh, mm = self.playout_config["day_start"]
        dt = datetime.datetime(y,m,d,hh,mm)
        self.load(start_time=time.mktime(dt.timetuple()))

    def toggle_mcr(self):
        if not self.mcr:
            return
        if self.mcr.isVisible():
            self.mcr.hide()
            self.app_state["show_mcr"] = False
        else:
            self.mcr.show()
            self.app_state["show_mcr"] = True
            self.load()

    def toggle_plugins(self):
        if not self.mcr:
            return
        if self.plugins.isVisible():
            self.plugins.hide()
            self.app_state["show_plugins"] = False
        else:
            self.plugins.show()
            self.app_state["show_plugins"] = True


    #
    # Search rundown
    #

    def find(self):
        text, result = QInputDialog.getText(
                self,
                "Rundown search",
                "Search query:",
                text=self.last_search
            )
        if result and text:
            self.do_find(text)
        else:
            self.last_search = ""

    def find_next(self):
        if self.last_search:
            self.do_find(self.last_search)
        else:
            self.find()

    def do_find(self, search_string, start_row=-1):
        self.last_search = search_string
        search_string = search_string.lower()
        if start_row == -1:
            for idx in self.view.selectionModel().selectedIndexes():
                if idx.row() > start_row:
                    start_row = idx.row()
        start_row += 1
        for i, row in enumerate(self.view.model().object_data[start_row:]):
            for key in ["title", "id/main"]:
                if str(row[key]).lower().find(search_string) > -1:
                    selection = QItemSelection()
                    i1 = self.view.model().index(i + start_row, 0, QModelIndex())
                    i2 = self.view.model().index(i + start_row, len(self.view.model().header_data)-1, QModelIndex())
                    self.view.scrollTo(i1 , QAbstractItemView.PositionAtTop)
                    selection.select(i1, i2)
                    self.view.selectionModel().select(selection, QItemSelectionModel.ClearAndSelect)
                    break
            else:
                continue
            break
        else:
            logging.warning("Not found: {}".format(self.last_search))
            self.view.clearSelection()

    #
    # Messaging
    #

    def seismic_handler(self, message):
        if self.main_window.current_module != self.main_window.rundown:
            return

        if message.method == "playout_status":
            if message.data["id_channel"] != self.id_channel:
                return

            if message.data["current_item"] != self.current_item:
                self.current_item = message.data["current_item"]
                self.view.model().refresh_items([self.current_item])

            if message.data["cued_item"] != self.cued_item:
                model = self.view.model()
                self.cued_item = message.data["cued_item"]
                for obj in model.object_data:
                    if obj.object_type == "item" and obj.id == self.cued_item:
                        if self.mcr and self.mcr.isVisible():
                            self.load()
                        else:
                            self.view.model().refresh_items([self.current_item])
                        break

            if self.mcr:
                self.mcr.seismic_handler(message)

        elif message.method == "objects_changed":
            if message.data["object_type"] == "event":
                for id_event in message.data["objects"]:
                    if id_event in self.view.model().event_ids:
                        logging.debug("Event id {} has been changed. Reloading rundown.".format(id_event))
                        self.load()
                        break
            elif message.data["object_type"] == "asset":
                self.refresh_assets(*message.data["objects"])

        elif message.method == "job_progress":
            if self.playout_config.get("send_action", 0) == message.data["id_action"]:

                model = self.view.model()
                for row, obj in enumerate(model.object_data):
                    if obj["id_asset"] == message.data["id_asset"]:
                        model.object_data[row]["transfer_progress"] = message.data["progress"]
                        model.dataChanged.emit(model.index(row, 0), model.index(row, len(model.header_data)-1))


    def refresh_assets(self, *assets):
        model = self.view.model()
        model.refresh_assets(assets)
