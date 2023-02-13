import json
import time

from nxtools import logging, format_time

import firefly

from firefly.api import api
from firefly.dialogs.rundown import PlaceholderDialog, SubclipSelectDialog
from firefly.objects import Asset, Item, Event, asset_cache
from firefly.view import FireflyViewModel
from firefly.qt import Qt, QApplication, QUrl, QMimeData

DEFAULT_COLUMNS = [
    "title",
    "id/main",
    "duration",
    "status",
    "run_mode",
    "scheduled_time",
    "broadcast_time",
    "rundown_difference",
    "mark_in",
    "mark_out",
]


class RundownModel(FireflyViewModel):
    def __init__(self, *args, **kwargs):
        super(RundownModel, self).__init__(*args, **kwargs)
        self.event_ids = []
        self.load_start_time = 0

    @property
    def id_channel(self):
        return self.parent().id_channel

    @property
    def start_time(self):
        return self.parent().start_time

    @property
    def current_item(self):
        return self.parent().current_item

    @property
    def cued_item(self):
        return self.parent().cued_item

    def load(self, callback=None):
        self.load_start_time = time.time()
        self.parent().setCursor(Qt.CursorShape.BusyCursor)
        self.current_callback = callback
        api.rundown(
            self.load_callback,
            id_channel=self.id_channel,
            date=format_time(self.start_time, "%Y-%m-%d"),
        )

    def load_callback(self, response):
        self.parent().setCursor(Qt.CursorShape.ArrowCursor)
        if not response:
            logging.error(response.message)
            return

        QApplication.processEvents()
        self.parent().setCursor(Qt.CursorShape.WaitCursor)
        self.beginResetModel()
        logging.info("Loading rundown. Please wait...")

        required_assets = []

        self.header_data = (
            firefly.settings.get_playout_channel(self.id_channel).rundown_columns
            or DEFAULT_COLUMNS
        )

        self.object_data = []
        self.event_ids = []

        i = 0
        for row in response["rows"]:
            row["rundown_row"] = 1
            row["rundown_scheduled"] = row["scheduled_time"]
            row["rundown_broadcast"] = row["broadcast_time"]
            row["rundown_difference"] = row["broadcast_time"] - row["scheduled_time"]

            if row["type"] == "event":
                self.object_data.append(Event(meta=row))
                i += 1
                self.event_ids.append(row["id"])
                if not row["duration"]:
                    meta = {"title": "(Empty event)", "id_bin": row["id_bin"]}
                    self.object_data.append(Item(meta=meta))
                    i += 1
            elif row["type"] == "item":
                item = Item(meta=row)
                item.id_channel = self.id_channel
                if row["id_asset"]:
                    item._asset = asset_cache.get(row["id_asset"])
                    required_assets.append([row["id_asset"], row["asset_mtime"]])
                else:
                    item._asset = False
                self.object_data.append(item)
                i += 1
            else:
                continue

        asset_cache.request(required_assets)

        self.endResetModel()
        self.parent().setCursor(Qt.CursorShape.ArrowCursor)
        logging.goodnews(
            f"Rundown loaded in {time.time() - self.load_start_time:.03f}s"
        )

        if self.current_callback:
            self.current_callback()

    def refresh_assets(self, assets):
        for row in range(len(self.object_data)):
            if (
                self.object_data[row].object_type == "item"
                and self.object_data[row]["id_asset"] in assets
            ):
                self.object_data[row]._asset = asset_cache.get(
                    self.object_data[row]["id_asset"]
                )
                self.dataChanged.emit(
                    self.index(row, 0), self.index(row, len(self.header_data) - 1)
                )

    def refresh_items(self, items):
        for row, obj in enumerate(self.object_data):
            if (
                self.object_data[row].id in items
                and self.object_data[row].object_type == "item"
            ):
                self.dataChanged.emit(
                    self.index(row, 0), self.index(row, len(self.header_data) - 1)
                )
                break

    def flags(self, index):
        flags = super(RundownModel, self).flags(index)
        if index.isValid():
            obj = self.object_data[index.row()]
            if obj.id and obj.object_type == "item":
                flags |= Qt.ItemFlag.ItemIsDragEnabled  # Itemy se daji dragovat
        else:
            flags = Qt.ItemFlag.ItemIsDropEnabled  # Dropovat se da jen mezi rowy
        return flags

    def mimeTypes(self):
        return ["application/nx.asset", "application/nx.item"]

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def mimeData(self, indices):
        rows = []
        for index in indices:
            if index.row() in rows:
                continue
            if not index.isValid():
                continue
            rows.append(index.row())

        data = [self.object_data[row].meta for row in rows]
        urls = [
            QUrl.fromLocalFile(self.object_data[row].file_path)
            for row in rows
            if self.object_data[row].file_path
        ]

        try:
            mimeData = QMimeData()
            mimeData.setData("application/nx.item", json.dumps(data).encode("ascii"))
            mimeData.setUrls(urls)
        except Exception:
            return
        return mimeData

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.DropAction.IgnoreAction:
            return True

        if not self.parent().parent().edit_enabled:
            return True

        if row < 1:
            return False

        drop_objects = []
        if data.hasFormat("application/nx.item"):
            d = data.data("application/nx.item").data()
            items = json.loads(d.decode("ascii"))
            if not items or items[0].get("rundown_row", "") in [row, row - 1]:
                return False
            else:
                for obj in items:
                    if action == Qt.DropAction.CopyAction:
                        obj["id"] = False
                    elif not obj.get("id", False):
                        item_role = obj.get("item_role", False)
                        if item_role in ["live", "placeholder"]:
                            dlg = PlaceholderDialog(self.parent(), obj)
                            dlg.exec()
                            if not dlg.ok:
                                return False
                            for key in dlg.meta:
                                obj[key] = dlg.meta[key]
                        elif item_role in ["lead_in", "lead_out"]:
                            pass
                        else:
                            continue
                    drop_objects.append(Item(meta=obj))

        elif data.hasFormat("application/nx.asset"):
            d = data.data("application/nx.asset").data()
            items = json.loads(d.decode("ascii"))
            for asset_data in items:
                asset = Asset(meta=asset_data)
                drop_objects.append(asset)
        else:
            return False

        sorted_items = []
        i = row - 1
        to_bin = self.object_data[i]["id_bin"]

        # Apend heading items

        while i >= 1:
            current_object = self.object_data[i]
            if (
                current_object.object_type != "item"
                or current_object["id_bin"] != to_bin
            ):
                break
            p_item = current_object.id
            if p_item not in [item.id for item in drop_objects]:
                if p_item:
                    sorted_items.append({"type": "item", "id": p_item})
            i -= 1
        sorted_items.reverse()

        # Append drop

        for obj in drop_objects:
            if data.hasFormat("application/nx.item"):
                sorted_items.append({"type": "item", "id": obj.id, "meta": obj.meta})

            elif data.hasFormat("application/nx.asset"):
                if obj["subclips"]:
                    dlg = SubclipSelectDialog(self.parent(), obj)
                    dlg.exec()
                    if dlg.ok:
                        for meta in dlg.result:
                            sorted_items.append(
                                {
                                    "type": "asset",
                                    "id": obj.id,
                                    "meta": meta,
                                }
                            )

                else:  # Asset does not have subclips
                    meta = {}
                    if obj["mark_in"] or obj["mark_out"]:
                        meta["mark_in"] = obj["mark_in"]
                        meta["mark_out"] = obj["mark_out"]

                    sorted_items.append({"type": "asset", "id": obj.id, "meta": meta})

        # Append trailing items

        i = row
        while i < len(self.object_data):
            current_object = self.object_data[i]
            if (
                current_object.object_type != "item"
                or current_object["id_bin"] != to_bin
            ):
                break
            p_item = current_object.id
            if p_item not in [item.id for item in drop_objects]:
                if p_item:
                    sorted_items.append({"type": "item", "id": p_item})
            i += 1

        #
        # Send order query
        #

        if not sorted_items:
            return
        self.parent().setCursor(Qt.CursorShape.BusyCursor)
        QApplication.processEvents()
        api.order(
            self.order_callback,
            id_channel=self.id_channel,
            bin=to_bin,
            order=sorted_items,
        )
        return False

    def order_callback(self, response):
        self.parent().setCursor(Qt.CursorShape.ArrowCursor)
        if not response:
            logging.error("Unable to change bin order: {}".format(response.message))
            return False
        self.load()
        return False
