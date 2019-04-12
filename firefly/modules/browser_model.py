from firefly import *

DEFAULT_HEADER_DATA = ["title", "duration", "id_folder"]

class BrowserModel(FireflyViewModel):
    def load(self, **kwargs):
        start_time = time.time()
        self.beginResetModel()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.object_data = []
        try:
            self.header_data = config["views"][kwargs["id_view"]]["columns"]
        except KeyError:
            self.header_data = DEFAULT_HEADER_DATA

        search_query = kwargs
        search_query["result"] = ["id", "mtime"]
        response = api.get(**search_query)
        if not response:
            logging.error(response.message)
        else:
            if asset_cache.request(response.data):
                self.object_data = [asset_cache[row[0]] for row in response.data]
        self.endResetModel()
        QApplication.restoreOverrideCursor()

    def flags(self,index):
        flags = super(BrowserModel, self).flags(index)
        if index.isValid():
            if self.object_data[index.row()].id:
                flags |= Qt.ItemIsDragEnabled
        return flags

    def mimeTypes(self):
        return ["application/nx.asset"]

    def mimeData(self, indices):
        rows = []
        for index in indices:
            if index.row() in rows:
                continue
            if not index.isValid():
                continue
            rows.append(index.row())

        data = [self.object_data[row].meta for row in rows]
        paths = [self.object_data[row].file_path for row in rows if self.object_data[row].file_path]
        urls = [QUrl.fromLocalFile(path) for path in paths]

        try:
            mimeData = QMimeData()
            mimeData.setData(
                    "application/nx.asset",
                    json.dumps(data).encode("ascii")
                )
            mimeData.setUrls(urls)
            return mimeData
        except Exception:
            log_traceback()
            return
