import functools

from firefly import *
from firefly.dialogs.rundown import *

DEFAULT_COLUMNS = [
        "title",
        "id/main",
        "duration",
        "status",
        "run_mode",
        "rundown_scheduled",
        "rundown_broadcast",
        "rundown_difference",
        "mark_in",
        "mark_out",
    ]


class RundownModel(FireflyViewModel):
    def __init__(self, *args, **kwargs):
        super(RundownModel, self).__init__(*args, **kwargs)
        self.event_ids = []

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

    def load(self, **kwargs):
        load_start_time = time.time()
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        logging.info("Loading rundown. Please wait...")

        response = api.rundown(id_channel=self.id_channel, start_time=self.start_time)
        if not response:
            QApplication.restoreOverrideCursor()
            return

        reset = True
        required_assets = []
        self.beginResetModel()

        self.header_data = DEFAULT_COLUMNS
        self.object_data = []
        self.event_ids = []

        i = 0
        for row in response.data:
            row["rundown_row"] = i
            if row["object_type"] == "event":
                self.object_data.append(Event(meta=row))
                i += 1
                self.event_ids.append(row["id"])
                if row["is_empty"]:
                    self.object_data.append(Item(meta={
                            "title" : "(Empty event)",
                            "id_bin" : row["id_bin"]
                        }))
                    i += 1
            elif row["object_type"] == "item":
                item = Item(meta=row)
                item.id_channel = self.id_channel
                if row["id_asset"]:
                    required_assets.append([row["id_asset"], row["asset_mtime"]])
                else:
                    item._asset = False
                self.object_data.append(item)
                i += 1
            else:
                continue

        asset_cache.request(required_assets)

        if reset:
            self.endResetModel()
        elif changed_rows:
            self.dataChanged.emit(
                    self.index(min(changed_rows), 0),
                    self.index(max(changed_rows), len(self.header_data)-1)
                )

        QApplication.restoreOverrideCursor()
        logging.goodnews(
                "{} rows of {} rundown loaded in {:.03f}".format(
                    len(response.data),
                    format_time(self.start_time, "%Y-%m-%d"),
                    time.time() - load_start_time
                )
            )


    def refresh_assets(self, assets):
        for row in range(len(self.object_data)):
            if self.object_data[row].object_type == "item" and self.object_data[row]["id_asset"] in assets:
                self.object_data[row]._asset = asset_cache[self.object_data[row]["id_asset"]]
                self.dataChanged.emit(self.index(row, 0), self.index(row, len(self.header_data)-1))

    def refresh_items(self, items):
        for row, obj in enumerate(self.object_data):
            if self.object_data[row].id in items and self.object_data[row].object_type == "item":
                self.dataChanged.emit(self.index(row, 0), self.index(row, len(self.header_data)-1))
                break


    def flags(self,index):
        flags = super(RundownModel, self).flags(index)
        if index.isValid():
            obj = self.object_data[index.row()]
            if obj.id and obj.object_type == "item":
                flags |= Qt.ItemIsDragEnabled # Itemy se daji dragovat
        else:
            flags = Qt.ItemIsDropEnabled # Dropovat se da jen mezi rowy
        return flags

    def mimeTypes(self):
        return ["application/nx.asset", "application/nx.item"]

    def mimeData(self, indices):
        rows = []
        for index in indices:
            if index.row() in rows:
                continue
            if not index.isValid():
                continue
            rows.append(index.row())

        data = [self.object_data[row].meta for row in rows]
        urls = [QUrl.fromLocalFile(self.object_data[row].file_path) for row in rows if self.object_data[row].file_path]

        mimeData = QMimeData()

        mimeData.setData("application/nx.item", json.dumps(data).encode("ascii"))
        mimeData.setUrls(urls)
        return mimeData


    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True

        if not user.has_right("rundown_edit", self.id_channel):
            logging.info("You are not allowed to modify this rundown")
            return True

        if row < 1:
            return False

        drop_objects = []
        if data.hasFormat("application/nx.item"):
            d = data.data("application/nx.item").data()
            items = json.loads(d.decode("ascii"))
            if not items or items[0].get("rundown_row","") in [row, row-1]:
                return False
            else:
                for obj in items:
                    if not obj.get("id", False):
                        item_role = obj.get("item_role", False)
                        if item_role in ["live", "placeholder"]:
                            dlg = PlaceholderDialog(self.parent(), obj)
                            dlg.exec_()
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
        i = row-1
        to_bin = self.object_data[i]["id_bin"]

        # Apend heading items

        while i >= 1:
            current_object = self.object_data[i]
            if current_object.object_type != "item" or current_object["id_bin"] != to_bin:
                break
            p_item = current_object.id
            if not p_item in [item.id for item in drop_objects]:
                if p_item:
                    sorted_items.append({"object_type" : "item", "id_object" : p_item, "meta" : {}})
            i-=1
        sorted_items.reverse()

        # Append drop

        for obj in drop_objects:
            if data.hasFormat("application/nx.item"):
                sorted_items.append({"object_type" : "item", "id_object" : obj.id, "meta" : obj.meta})

            elif data.hasFormat("application/nx.asset"):
                metas = []
                if obj["subclips"]:
                    dlg = SubclipSelectDialog(self.parent(), obj)
                    dlg.exec_()
                    if dlg.ok:
                        for meta in dlg.result:
                            sorted_items.append({"object_type" : "asset", "id_object" : obj.id, "meta" : meta})


                else: # Asset does not have subclips
                    meta = {}
                    if obj["mark_in"]:
                        meta["mark_in"] = obj["mark_in"]
                        meta["mark_out"] = obj["mark_out"]

                    sorted_items.append({"object_type" : "asset", "id_object" : obj.id, "meta" : meta})


        # Append trailing items

        i = row
        while i < len(self.object_data):
            current_object = self.object_data[i]
            if current_object.object_type != "item" or current_object["id_bin"] != to_bin:
                break
            p_item = current_object.id
            if not p_item in [item.id for item in drop_objects]:
                if p_item:
                    sorted_items.append({"object_type" : "item", "id_object" : p_item, "meta" : {}})
            i+=1

        #
        # Send order query
        #

        sorted_items = [item for item in sorted_items]# if item["id_object"]]

        if sorted_items:
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            response = api.order(
                    id_channel=self.id_channel,
                    id_bin=to_bin,
                    order=sorted_items
                )
            QApplication.restoreOverrideCursor()
            if not response:
                logging.error("Unable to change bin order: {}".format(response.message))
        return True
