import math
from firefly import *

DEFAULT_HEADER_DATA = ["title", "duration", "id_folder"]
RECORDS_PER_PAGE = 1000

class BrowserModel(FireflyViewModel):
    def load(self, callback, **kwargs):
        start_time = time.time()

        try:
            self.header_data = config["views"][kwargs["id_view"]]["columns"]
        except KeyError:
            self.header_data = DEFAULT_HEADER_DATA

        search_query = kwargs
        search_query["result"] = ["id", "mtime"]
        response = api.get(
                functools.partial(self.load_callback, callback),
                **search_query,
                count=True,
                limit=RECORDS_PER_PAGE,
                offset=(self.parent().current_page - 1) * RECORDS_PER_PAGE
            )


    def load_callback(self, callback, response):
        self.beginResetModel()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.object_data = []

        if not response:
            logging.error(response.message)
        else:
            page_count = int(math.ceil(response["count"] / RECORDS_PER_PAGE))
            self.parent().set_num_pages(page_count)
            asset_cache.request(response.data)
            self.object_data = [asset_cache.get(row[0]) for row in response.data]

        self.endResetModel()
        QApplication.restoreOverrideCursor()
        callback()


    def headerData(self, col, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return format_header(self.header_data[col])
            elif role == Qt.ToolTipRole:
                desc = format_description(self.header_data[col])
                return "<p>{}</p>".format(desc) if desc else None
            elif role == Qt.DecorationRole:
                order, trend = self.parent().current_order
                if self.header_data[col] == order:
                    return pix_lib[["smallarrow-up", "smallarrow-down"][int(trend=="desc")]]
        return None


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
