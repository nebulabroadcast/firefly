import json
import functools

from nxtools import logging, log_traceback

import firefly

from firefly.objects import Asset
from firefly.api import api
from firefly.view import FireflyViewModel, format_header, format_description
from firefly.qt import (
    Qt,
    QApplication,
    QUrl,
    QMimeData,
    pixlib,
)

DEFAULT_HEADER_DATA = ["title", "duration", "id_folder"]
RECORDS_PER_PAGE = 1000


class BrowserModel(FireflyViewModel):
    def load(self, callback, **kwargs):

        try:
            id_view = kwargs["id_view"]
            self.header_data = firefly.settings.get_view(id_view).columns
        except KeyError:
            self.header_data = DEFAULT_HEADER_DATA

        api.browse(
            functools.partial(self.load_callback, callback),
            # TODO: V6
            view=kwargs["id_view"],
            query=kwargs["fulltext"],
            limit=RECORDS_PER_PAGE + 1,
            order_by=kwargs["order_by"],
            order_dir=kwargs["order_dir"],
            offset=(self.parent().current_page - 1) * RECORDS_PER_PAGE,
        )

    def load_callback(self, callback, response):
        self.beginResetModel()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        if not response:
            logging.error(response.message)

        # Pagination

        current_page = self.parent().current_page

        if len(response.data) > RECORDS_PER_PAGE:
            page_count = current_page + 1
        elif len(response.data) == 0:
            page_count = max(1, current_page - 1)
        else:
            page_count = current_page

        if current_page > page_count:
            current_page = page_count

        # Replace object data

        if len(response.data) > RECORDS_PER_PAGE:
            response.data.pop(-1)
        self.object_data = [Asset(meta=m) for m in response.data]

        self.parent().set_page(current_page, page_count)
        self.endResetModel()
        QApplication.restoreOverrideCursor()

        callback()

    def headerData(
        self,
        col,
        orientation=Qt.Orientation.Horizontal,
        role=Qt.ItemDataRole.DisplayRole,
    ):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return format_header(self.header_data[col])
            elif role == Qt.ItemDataRole.ToolTipRole:
                desc = format_description(self.header_data[col])
                return "<p>{}</p>".format(desc) if desc else None
            elif role == Qt.ItemDataRole.DecorationRole:
                sq = self.parent().parent().search_query
                if self.header_data[col] == sq["order_by"]:
                    return pixlib[
                        ["smallarrow-up", "smallarrow-down"][
                            int(sq["order_dir"] == "desc")
                        ]
                    ]
        return None

    def flags(self, index):
        flags = super(BrowserModel, self).flags(index)
        if index.isValid():
            if self.object_data[index.row()].id:
                flags |= Qt.ItemFlag.ItemIsDragEnabled
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
        paths = [
            self.object_data[row].file_path
            for row in rows
            if self.object_data[row].file_path
        ]
        urls = [QUrl.fromLocalFile(path) for path in paths]

        try:
            mimeData = QMimeData()
            mimeData.setData("application/nx.asset", json.dumps(data).encode("ascii"))
            mimeData.setUrls(urls)
            return mimeData
        except Exception:
            log_traceback()
            return
