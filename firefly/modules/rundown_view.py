import functools
from firefly import *

from .rundown_model import RundownModel

from firefly.dialogs.event import *
from firefly.dialogs.rundown import *
from firefly.dialogs.send_to import *

class RundownView(FireflyView):
    def __init__(self, parent):
        super(RundownView, self).__init__(parent)
        self.activated.connect(self.on_activate)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setModel(RundownModel(self))
        self.focus_enabled = True

    @property
    def id_channel(self):
        return self.parent().id_channel

    @property
    def playout_config(self):
        return config["playout_channels"][self.id_channel]

    @property
    def start_time(self):
        return self.parent().start_time

    @property
    def current_item(self):
        return self.parent().current_item

    @property
    def cued_item(self):
        return self.parent().cued_item

    def load(self):
        self.model().load()

    def selectionChanged(self, selected, deselected):
        rows = []
        self.selected_objects = []
        tot_dur = 0

        for idx in self.selectionModel().selectedIndexes():
            row = idx.row()
            if row in rows:
                continue
            rows.append(row)
            obj = self.model().object_data[row]
            self.selected_objects.append(obj)
            if obj.object_type in ["asset", "item"]:
                tot_dur += obj.duration

        if self.selected_objects and self.focus_enabled:
            self.parent().main_window.focus(self.selected_objects[0])
            if len(self.selected_objects) == 1 and self.selected_objects[0].object_type == "item" and self.selected_objects[0]["id_asset"]:
                asset = self.selected_objects[0].asset
                times = len([obj for obj in self.model().object_data if obj.object_type == "item" and obj["id_asset"] == asset.id])
                logging.info("{} is scheduled {}x in this rundown".format(asset, times))
            if len(self.selected_objects) > 1 and tot_dur:
                logging.info("{} objects selected. Total duration {}".format(len(self.selected_objects), s2time(tot_dur)))

        super(FireflyView, self).selectionChanged(selected, deselected)

    #
    # Rundown actions
    #

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.on_delete()
        FireflyView.keyPressEvent(self, event)


    def contextMenuEvent(self, event):
        obj_set = list(set([itm.object_type for itm in self.selected_objects]))
        menu = QMenu(self)

        if len(obj_set) == 1:
            if len(self.selected_objects) == 1:
                if self.selected_objects[0]["item_role"] == "placeholder":
                    solvers = self.playout_config.get("solvers", [])
                    if solvers:
                        solver_menu = menu.addMenu("Solve using...")
                        for solver in solvers:
                            action_solve = QAction(solver.capitalize(), self)
                            action_solve.setStatusTip("Solve this placeholder using {}".format(solver))
                            action_solve.triggered.connect(functools.partial(self.on_solve, solver))
                            solver_menu.addAction(action_solve)

                if obj_set[0] == "item" and self.selected_objects[0]["id_asset"]:
                    action_trim = QAction("Trim", self)
                    action_trim.setStatusTip('Trim selected item')
                    action_trim.triggered.connect(self.on_trim)
                    menu.addAction(action_trim)

            if obj_set[0] == "item" and (self.selected_objects[0]["id_asset"] or self.selected_objects[0]["item_role"] == "live"):

                mode_menu = menu.addMenu("Run mode")

                action_mode_auto = QAction('&Auto', self)
                action_mode_auto.setStatusTip('Set run mode to auto')
                action_mode_auto.setCheckable(True)
                action_mode_auto.setChecked(self.selected_objects[0]["run_mode"] == RUN_AUTO)
                action_mode_auto.triggered.connect(functools.partial(self.on_set_mode, RUN_AUTO))
                mode_menu.addAction(action_mode_auto)

                action_mode_manual = QAction('&Manual', self)
                action_mode_manual.setStatusTip('Set run mode to manual')
                action_mode_manual.setCheckable(True)
                action_mode_manual.setChecked(self.selected_objects[0]["run_mode"] == RUN_MANUAL)
                action_mode_manual.triggered.connect(functools.partial(self.on_set_mode, RUN_MANUAL))
                mode_menu.addAction(action_mode_manual)

                action_mode_skip = QAction('&Skip', self)
                action_mode_skip.setStatusTip('Set run mode to skip')
                action_mode_skip.setCheckable(True)
                action_mode_skip.setChecked(self.selected_objects[0]["run_mode"] == RUN_SKIP)
                action_mode_skip.triggered.connect(functools.partial(self.on_set_mode, RUN_SKIP))
                mode_menu.addAction(action_mode_skip)

                if self.selected_objects[0]["id_asset"]:
                    mode_menu.addSeparator()
                    action_mode_loop = QAction('&Loop', self)
                    action_mode_loop.setStatusTip('Loop item')
                    action_mode_loop.setCheckable(True)
                    action_mode_loop.setChecked(bool(self.selected_objects[0]["loop"]))
                    action_mode_loop.triggered.connect(self.on_set_loop)
                    mode_menu.addAction(action_mode_loop)


            elif obj_set[0] == "event" and len(self.selected_objects) == 1:
                mode_menu = menu.addMenu("Run mode")

                action_mode_auto = QAction('&Auto', self)
                action_mode_auto.setStatusTip('Set run mode to auto')
                action_mode_auto.setCheckable(True)
                action_mode_auto.setChecked(self.selected_objects[0]["run_mode"] == RUN_AUTO)
                action_mode_auto.triggered.connect(functools.partial(self.on_set_mode, RUN_AUTO))
                mode_menu.addAction(action_mode_auto)

                action_mode_manual = QAction('&Manual', self)
                action_mode_manual.setStatusTip('Set run mode to manual')
                action_mode_manual.setCheckable(True)
                action_mode_manual.setChecked(self.selected_objects[0]["run_mode"] == RUN_MANUAL)
                action_mode_manual.triggered.connect(functools.partial(self.on_set_mode, RUN_MANUAL))
                mode_menu.addAction(action_mode_manual)

                action_mode_soft = QAction('&Soft', self)
                action_mode_soft.setStatusTip('Set run mode to soft')
                action_mode_soft.setCheckable(True)
                action_mode_soft.setChecked(self.selected_objects[0]["run_mode"] == RUN_SOFT)
                action_mode_soft.triggered.connect(functools.partial(self.on_set_mode, RUN_SOFT))
                mode_menu.addAction(action_mode_soft)

                action_mode_hard = QAction('&Hard', self)
                action_mode_hard.setStatusTip('Set run mode to hard')
                action_mode_hard.setCheckable(True)
                action_mode_hard.setChecked(self.selected_objects[0]["run_mode"] == RUN_HARD)
                action_mode_hard.triggered.connect(functools.partial(self.on_set_mode, RUN_HARD))
                mode_menu.addAction(action_mode_hard)


        if "item" in obj_set:
            if len(self.selected_objects) == 1 and self.selected_objects[0]["item_role"] in ["placeholder", "lead_in", "lead_out", "live"]:
                pass
            else:
                action_send_to = QAction('&Send to...', self)
                action_send_to.setStatusTip('Create action for selected asset(s)')
                action_send_to.triggered.connect(self.on_send_to)
                menu.addAction(action_send_to)

        if "event" in obj_set:
            pass

        if len(obj_set) > 0:
            menu.addSeparator()

            action_delete = QAction('&Delete', self)
            action_delete.setStatusTip('Delete selected object')
            action_delete.triggered.connect(self.on_delete)
            menu.addAction(action_delete)

            if len(self.selected_objects) == 1:
                if "event" in obj_set:
                    action_edit = QAction('Edit', self)
                    action_edit.triggered.connect(self.on_edit_event)
                    menu.addAction(action_edit)
                elif self.selected_objects[0]["item_role"] in ["placeholder", "live"]:
                    action_edit = QAction('Edit', self)
                    action_edit.triggered.connect(self.on_edit_item)
                    menu.addAction(action_edit)

        menu.exec_(event.globalPos())



    def on_set_loop(self):
        if not self.parent().can_edit:
            logging.error("You are not allowed to modify this rundown")
            return
        mode = not self.selected_objects[0]["loop"]
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        response = api.set(object_type=self.selected_objects[0].object_type, objects=[obj.id for obj in self.selected_objects], data={"loop" : mode})
        QApplication.restoreOverrideCursor()
        if not response:
            logging.error(response.message)
            return
        self.load()



    def on_set_mode(self, mode):
        if not self.parent().can_edit:
            logging.error("You are not allowed to modify this rundown")
            return
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        response = api.set(object_type=self.selected_objects[0].object_type, objects=[obj.id for obj in self.selected_objects], data={"run_mode":mode})
        QApplication.restoreOverrideCursor()
        if not response:
            logging.error(response.message)
            return
        self.load()

    def on_trim(self):
        item = self.selected_objects[0]
        trim_dialog(item)


    def on_solve(self, solver):
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        response = api.solve(id_item=self.selected_objects[0]["id"], solver=solver)
        QApplication.restoreOverrideCursor()
        if not response:
            logging.error(response.message)
        self.load()


    def on_delete(self):
        items = list(set([obj.id for obj in self.selected_objects if obj.object_type == "item"]))
        events  = list(set([obj.id for obj in self.selected_objects if obj.object_type == "event"]))

        if items and not self.parent().can_edit:
            logging.error("You are not allowed to modify this rundown items")
            return
        elif events and not self.parent().can_schedule:
            logging.error("You are not allowed to modify this rundown blocks")
            return


        if events or len(items) > 10:
            ret = QMessageBox.question(
                    self,
                    "Delete",
                    "Do you REALLY want to delete {} items and {} events?\nThis operation CANNOT be undone".format(len(items), len(events)),
                    QMessageBox.Yes | QMessageBox.No
                )

            if ret != QMessageBox.Yes:
                return

        if items:
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            response = api.delete(object_type="item", objects=items)
            QApplication.restoreOverrideCursor()
            if not response:
                logging.error(response.message)
                return
            else:
                logging.info("Item deleted: {}".format(response.message))

        if events:
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            response = api.schedule(delete=events, id_channel=self.parent().id_channel)
            QApplication.restoreOverrideCursor()
            if not response:
                logging.error(response.message)
                return
            else:
                logging.info("Event deleted: {}".format(response.message))

        self.selectionModel().clear()
        self.load()

    def on_send_to(self):
        objs = set([obj for obj in self.selected_objects if obj.object_type == "item" and obj["id_asset"]])
        send_to_dialog(objs)

    def on_edit_item(self):
        objs = [obj for obj in self.selected_objects if obj.object_type == "item" and obj["item_role"] in ["live", "placeholder"]]
        if not objs:
            return
        obj = objs[0]
        dlg = PlaceholderDialog(self, obj.meta)
        dlg.exec_()
        if not dlg.ok:
            return False
        data = {}
        for key in dlg.meta:
            if dlg.meta[key] != obj[key]:
                data[key] = dlg.meta[key]
        if not data:
            return
        response = api.set(
                object_type=obj.object_type,
                objects=[obj.id],
                data=data
            )
        if not response:
            logging.error(response.message)
            return
        self.load()

    def on_edit_event(self):
        objs = [obj for obj in self.selected_objects if obj.object_type == "event"]
        if event_dialog(event=objs[0]):
            self.load()

    def on_activate(self, mi):
        obj = self.model().object_data[mi.row()]
        can_mcr = user.has_right("mcr", self.id_channel)
        if obj.object_type == "item":

            if obj.id:
                if obj["item_role"] == "placeholder":
                    self.on_edit_item()

                elif self.parent().mcr and self.parent().mcr.isVisible() and can_mcr:
                    response = api.playout(timeout=1, action="cue", id_channel=self.id_channel, id_item=obj.id)
                    if not response:
                        logging.error(response.message)
                    self.clearSelection()



        # Event edit
        elif obj.object_type == "event" and (has_right("scheduler_view", self.id_channel) or has_right("scheduler_edit", self.id_channel)):
            self.on_edit_event()
        self.clearSelection()
