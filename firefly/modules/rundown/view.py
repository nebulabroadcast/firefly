from functools import partial
from nxtools import logging, s2time

import firefly

from firefly.api import api
from firefly.enum import RunMode
from firefly.qt import Qt, QAbstractItemView, QMenu, QAction, QApplication, QMessageBox
from firefly.view import FireflyView

from firefly.dialogs.event import show_event_dialog
from firefly.dialogs.send_to import show_send_to_dialog
from firefly.dialogs.rundown import PlaceholderDialog, show_trim_dialog

from .model import RundownModel


class RundownView(FireflyView):
    def __init__(self, parent):
        super(RundownView, self).__init__(parent)
        self.activated.connect(self.on_activate)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setModel(RundownModel(self))
        self.focus_enabled = True
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    @property
    def id_channel(self):
        return self.parent().id_channel

    @property
    def playout_config(self):
        return firefly.settings.get_playout_channel(self.id_channel)

    @property
    def start_time(self):
        return self.parent().start_time

    @property
    def current_item(self):
        return self.parent().current_item

    @property
    def cued_item(self):
        return self.parent().cued_item

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
            if (
                len(self.selected_objects) == 1
                and self.selected_objects[0].object_type == "item"
                and self.selected_objects[0]["id_asset"]
            ):
                asset = self.selected_objects[0].asset
                times = len(
                    [
                        obj
                        for obj in self.model().object_data
                        if obj.object_type == "item" and obj["id_asset"] == asset.id
                    ]
                )
                logging.info("{} is scheduled {}x in this rundown".format(asset, times))
            if len(self.selected_objects) > 1 and tot_dur:
                logging.info(
                    "{} objects selected. Total duration {}".format(
                        len(self.selected_objects), s2time(tot_dur)
                    )
                )

        super(FireflyView, self).selectionChanged(selected, deselected)

    #
    # Rundown actions
    #

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.on_delete()
        FireflyView.keyPressEvent(self, event)

    def contextMenuEvent(self, event):
        obj_set = list(set([itm.object_type for itm in self.selected_objects]))
        menu = QMenu(self)

        if len(obj_set) == 1:
            if len(self.selected_objects) == 1:
                if self.selected_objects[0]["item_role"] == "placeholder":
                    if solvers := self.playout_config.solvers:
                        solver_menu = menu.addMenu("Solve using...")
                        for solver in solvers:
                            action_solve = QAction(solver.capitalize(), self)
                            action_solve.setStatusTip(f"Solve using {solver}")
                            action_solve.triggered.connect(
                                partial(self.on_solve, solver)
                            )
                            solver_menu.addAction(action_solve)

                if obj_set[0] == "item" and self.selected_objects[0]["id_asset"]:
                    action_trim = QAction("Trim", self)
                    action_trim.setStatusTip("Trim selected item")
                    action_trim.triggered.connect(self.on_trim)
                    menu.addAction(action_trim)

            if obj_set[0] == "item" and (
                self.selected_objects[0]["id_asset"]
                or self.selected_objects[0]["item_role"] == "live"
            ):

                mode_menu = menu.addMenu("Run mode")

                action_mode_auto = QAction("&Auto", self)
                action_mode_auto.setStatusTip("Set run mode to auto")
                action_mode_auto.setCheckable(True)
                action_mode_auto.setChecked(
                    self.selected_objects[0]["run_mode"] == RunMode.RUN_AUTO
                )
                action_mode_auto.triggered.connect(
                    partial(self.on_set_mode, RunMode.RUN_AUTO)
                )
                mode_menu.addAction(action_mode_auto)

                action_mode_manual = QAction("&Manual", self)
                action_mode_manual.setStatusTip("Set run mode to manual")
                action_mode_manual.setCheckable(True)
                action_mode_manual.setChecked(
                    self.selected_objects[0]["run_mode"] == RunMode.RUN_MANUAL
                )
                action_mode_manual.triggered.connect(
                    partial(self.on_set_mode, RunMode.RUN_MANUAL)
                )
                mode_menu.addAction(action_mode_manual)

                action_mode_skip = QAction("&Skip", self)
                action_mode_skip.setStatusTip("Set run mode to skip")
                action_mode_skip.setCheckable(True)
                action_mode_skip.setChecked(
                    self.selected_objects[0]["run_mode"] == RunMode.RUN_SKIP
                )
                action_mode_skip.triggered.connect(
                    partial(self.on_set_mode, RunMode.RUN_SKIP)
                )
                mode_menu.addAction(action_mode_skip)

                if self.selected_objects[0]["id_asset"]:
                    mode_menu.addSeparator()
                    action_mode_loop = QAction("&Loop", self)
                    action_mode_loop.setStatusTip("Loop item")
                    action_mode_loop.setCheckable(True)
                    action_mode_loop.setChecked(bool(self.selected_objects[0]["loop"]))
                    action_mode_loop.triggered.connect(self.on_set_loop)
                    mode_menu.addAction(action_mode_loop)

            elif obj_set[0] == "event" and len(self.selected_objects) == 1:
                mode_menu = menu.addMenu("Run mode")

                action_mode_auto = QAction("&Auto", self)
                action_mode_auto.setStatusTip("Set run mode to auto")
                action_mode_auto.setCheckable(True)
                action_mode_auto.setChecked(
                    self.selected_objects[0]["run_mode"] == RunMode.RUN_AUTO
                )
                action_mode_auto.triggered.connect(
                    partial(self.on_set_mode, RunMode.RUN_AUTO)
                )
                mode_menu.addAction(action_mode_auto)

                action_mode_manual = QAction("&Manual", self)
                action_mode_manual.setStatusTip("Set run mode to manual")
                action_mode_manual.setCheckable(True)
                action_mode_manual.setChecked(
                    self.selected_objects[0]["run_mode"] == RunMode.RUN_MANUAL
                )
                action_mode_manual.triggered.connect(
                    partial(self.on_set_mode, RunMode.RUN_MANUAL)
                )
                mode_menu.addAction(action_mode_manual)

                action_mode_soft = QAction("&Soft", self)
                action_mode_soft.setStatusTip("Set run mode to soft")
                action_mode_soft.setCheckable(True)
                action_mode_soft.setChecked(
                    self.selected_objects[0]["run_mode"] == RunMode.RUN_SOFT
                )
                action_mode_soft.triggered.connect(
                    partial(self.on_set_mode, RunMode.RUN_SOFT)
                )
                mode_menu.addAction(action_mode_soft)

                action_mode_hard = QAction("&Hard", self)
                action_mode_hard.setStatusTip("Set run mode to hard")
                action_mode_hard.setCheckable(True)
                action_mode_hard.setChecked(
                    self.selected_objects[0]["run_mode"] == RunMode.RUN_HARD
                )
                action_mode_hard.triggered.connect(
                    partial(self.on_set_mode, RunMode.RUN_HARD)
                )
                mode_menu.addAction(action_mode_hard)

        if "item" in obj_set:
            if len(self.selected_objects) == 1 and self.selected_objects[0][
                "item_role"
            ] in ["placeholder", "lead_in", "lead_out", "live"]:
                pass
            else:
                action_send_to = QAction("&Send to...", self)
                action_send_to.setStatusTip("Create action for selected asset(s)")
                action_send_to.triggered.connect(self.on_send_to)
                menu.addAction(action_send_to)

        if "event" in obj_set:
            pass

        if len(obj_set) > 0:
            menu.addSeparator()

            action_delete = QAction("&Delete", self)
            action_delete.setStatusTip("Delete selected object")
            action_delete.triggered.connect(self.on_delete)
            menu.addAction(action_delete)

            if len(self.selected_objects) == 1:
                if "event" in obj_set:
                    action_edit = QAction("Edit", self)
                    action_edit.triggered.connect(self.on_edit_event)
                    menu.addAction(action_edit)
                elif self.selected_objects[0]["item_role"] in ["placeholder", "live"]:
                    action_edit = QAction("Edit", self)
                    action_edit.triggered.connect(self.on_edit_item)
                    menu.addAction(action_edit)

        menu.exec(event.globalPos())

    def on_set_loop(self):
        if not self.parent().can_edit:
            logging.error("You are not allowed to modify this rundown")
            return
        mode = not self.selected_objects[0]["loop"]
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        print("loop:", mode)

        response = api.ops(
            operations=[
                {
                    "object_type": obj.object_type,
                    "id": obj.id,
                    "data": {"loop": mode},
                }
                for obj in self.selected_objects
            ]
        )

        QApplication.restoreOverrideCursor()
        if not response:
            logging.error(response.message)
            return
        self.model().load()

    def on_set_mode(self, mode):
        if not self.parent().can_edit:
            logging.error("You are not allowed to modify this rundown")
            return
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        response = api.ops(
            operations=[
                {
                    "object_type": obj.object_type,
                    "id": obj.id,
                    "data": {"run_mode": mode},
                }
                for obj in self.selected_objects
            ]
        )
        QApplication.restoreOverrideCursor()
        if not response:
            logging.error(response.message)
            return
        self.model().load()

    def on_trim(self):
        item = self.selected_objects[0]
        show_trim_dialog(self, item)
        self.model().load()

    def on_solve(self, solver):
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        response = api.solve(id_item=self.selected_objects[0]["id"], solver=solver)
        QApplication.restoreOverrideCursor()
        if not response:
            logging.error(response.message)
        self.model().load()
        self.parent().main_window.scheduler.load()

    def on_delete(self):
        items = list(
            set([obj.id for obj in self.selected_objects if obj.object_type == "item"])
        )
        events = list(
            set([obj.id for obj in self.selected_objects if obj.object_type == "event"])
        )

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
                "Do you REALLY want to delete "
                f"{len(items)} items and {len(events)} events?\n"
                "This operation CANNOT be undone",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if ret != QMessageBox.StandardButton.Yes:
                return

        if items:
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            response = api.delete(object_type="item", ids=items)
            QApplication.restoreOverrideCursor()
            if not response:
                logging.error(response.message)
                return
            else:
                logging.info("Item deleted: {}".format(response.message))

        if events:
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            response = api.schedule(delete=events, id_channel=self.parent().id_channel)
            QApplication.restoreOverrideCursor()
            if not response:
                logging.error(response.message)
                return
            else:
                logging.info("Event deleted: {}".format(response.message))

        self.selectionModel().clear()
        self.model().load()
        self.parent().main_window.scheduler.refresh_events(events)

    def on_send_to(self):
        objs = set(
            [
                obj
                for obj in self.selected_objects
                if obj.object_type == "item" and obj["id_asset"]
            ]
        )
        show_send_to_dialog(self, objs)
        self.model().load()

    def on_edit_item(self):
        objs = [
            obj
            for obj in self.selected_objects
            if obj.object_type == "item" and obj["item_role"] in ["live", "placeholder"]
        ]
        if not objs:
            return
        obj = objs[0]
        dlg = PlaceholderDialog(self, obj.meta)
        dlg.exec()
        if not dlg.ok:
            return False
        data = {}
        for key in dlg.meta:
            if dlg.meta[key] != obj[key]:
                data[key] = dlg.meta[key]
        if not data:
            return
        response = api.set(object_type=obj.object_type, id=obj.id, data=data)
        if not response:
            logging.error(response.message)
            return
        self.model().load()

    def on_edit_event(self):
        objs = [obj for obj in self.selected_objects if obj.object_type == "event"]
        if show_event_dialog(self, event=objs[0]):
            self.model().load()
        self.parent().main_window.scheduler.load()

    def on_activate(self, mi):
        obj = self.model().object_data[mi.row()]
        can_mcr = firefly.user.can("mcr", self.id_channel)
        if obj.object_type == "item":

            if obj.id:
                if obj["item_role"] == "placeholder":
                    self.on_edit_item()

                elif self.parent().mcr and self.parent().mcr.isVisible() and can_mcr:
                    response = api.playout(
                        timeout=1,
                        action="cue",
                        id_channel=self.id_channel,
                        payload={"id_item" : obj.id},
                    )
                    if not response:
                        logging.error(response.message)
                    self.clearSelection()

        # Event edit
        elif obj.object_type == "event" and (
            firefly.user.can("scheduler_view", self.id_channel)
            or firefly.user.can("scheduler_edit", self.id_channel)
        ):
            self.on_edit_event()
        self.clearSelection()

    def dragMoveEvent(self, event):
        super(RundownView, self).dragMoveEvent(event)
        if event.mimeData().hasFormat("application/nx.item"):
            if event.keyboardModifiers() & Qt.KeyboardModifier.AltModifier:
                event.setDropAction(Qt.DropAction.CopyAction)
            else:
                event.setDropAction(Qt.DropAction.MoveAction)
        elif event.mimeData().hasFormat("application/nx.asset"):
            event.setDropAction(Qt.DropAction.CopyAction)
        else:
            event.setDropAction(Qt.DropAction.IgnoreAction)
