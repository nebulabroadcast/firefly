import functools

from nxtools import format_time, logging

from firefly.api import api
from firefly.enum import Colors, JobState
from firefly.objects import asset_cache
from firefly.qt import QAction, QApplication, QColor, QMenu, Qt
from firefly.view import FireflyView, FireflyViewModel

DEFAULT_HEADER_DATA = [
    "id",
    "title",
    "action",
    "service",
    "ctime",
    "stime",
    "etime",
    "progress",
]


def job_format(data, key):
    if key in ["ctime", "stime", "etime"]:
        if not data.get(key):
            return ""
        return format_time(data[key])
    elif key == "title":
        return asset_cache[data["id_asset"]]["title"]
    elif key == "action":
        return data["action_name"]
    elif key == "service":
        return data.get("service_name", "")
    elif key == "message":
        return data.get("message", "")
    elif key == "id":
        return str(data["id"])
    elif key == "progress":
        if data["status"] == 1:
            return f"{data['progress']:.02f}%"
        else:
            return {
                0: "Pending",
                1: "In progress",
                2: "Completed",
                3: "Failed",
                4: "Aborted",
                5: "Restarted",
                6: "Skipped",
            }[data["status"]]
    return "-"


header_format = {
    "id": "#",
    "title": "Title",
    "action": "Action",
    "service": "Service",
    "ctime": "Created",
    "stime": "Started",
    "etime": "Ended",
    "progress": "Progress",
}

colw = {
    "id": 50,
    "title": 200,
    "action": 80,
    "service": 160,
    "ctime": 150,
    "stime": 150,
    "etime": 150,
    "progress": 100,
}

colors = {
    JobState.PENDING: QColor(Colors.TEXT_NORMAL.value),
    JobState.IN_PROGRESS: QColor(Colors.TEXT_HIGHLIGHT.value),
    JobState.COMPLETED: QColor(Colors.TEXT_GREEN.value),
    JobState.FAILED: QColor(Colors.TEXT_RED.value),
    JobState.ABORTED: QColor(Colors.TEXT_RED.value),
    JobState.RESTART: QColor(Colors.TEXT_NORMAL.value),
    JobState.SKIPPED: QColor(Colors.TEXT_FADED.value),
}


class JobsModel(FireflyViewModel):
    def __init__(self, *args, **kwargs):
        super(JobsModel, self).__init__(*args, **kwargs)
        self.request_data = {"view": "active"}

    def headerData(
        self,
        col,
        orientation=Qt.Orientation.Horizontal,
        role=Qt.ItemDataRole.DisplayRole,
    ):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return header_format[self.header_data[col]]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        obj = self.object_data[row]
        key = self.header_data[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            return job_format(obj, key)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return f"{obj['message']}\n\n{asset_cache[obj['id_asset']]}"
        elif role == Qt.ItemDataRole.ForegroundRole:
            if key == "progress":
                return colors[obj["status"]]

        return None

    def load(self, **kwargs):
        self.request_data.update(kwargs)
        self.beginResetModel()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        data = []
        response = api.jobs(**self.request_data)
        if not response:
            logging.error(response.message)
        else:
            request_assets = []
            for row in response["jobs"]:
                data.append(row)
                request_assets.append([row["id_asset"], 0])
            asset_cache.request(request_assets)
        self.object_data = data
        self.endResetModel()
        QApplication.restoreOverrideCursor()


class FireflyJobsView(FireflyView):
    def __init__(self, parent):
        super(FireflyJobsView, self).__init__(parent)
        self.model = JobsModel(self)
        self.model.header_data = DEFAULT_HEADER_DATA
        self.setModel(self.model)
        for i, h in enumerate(self.model.header_data):
            if h in colw:
                self.horizontalHeader().resizeSection(i, colw[h])

    def selectionChanged(self, selected, deselected):
        super(FireflyView, self).selectionChanged(selected, deselected)
        sel = self.selected_jobs
        if len(sel) == 1:
            self.parent().main_window.focus(asset_cache[sel[0]["id_asset"]])

    @property
    def selected_jobs(self):
        used = []
        result = []
        for idx in self.selectionModel().selectedIndexes():
            i = idx.row()
            if i not in used:
                used.append(i)
                result.append(self.model.object_data[i])
        return result

    def contextMenuEvent(self, event):
        jobs = [k["id"] for k in self.selected_jobs]
        if not jobs:
            return

        menu = QMenu(self)

        action_restart = QAction("Restart", self)
        action_restart.setStatusTip("Restart selected jobs")
        action_restart.triggered.connect(functools.partial(self.on_restart, jobs))
        menu.addAction(action_restart)

        action_abort = QAction("Abort", self)
        action_abort.setStatusTip("Abort selected jobs")
        action_abort.triggered.connect(functools.partial(self.on_abort, jobs))
        menu.addAction(action_abort)

        menu.exec(event.globalPos())

    def on_restart(self, jobs):
        for job in jobs:
            response = api.jobs(restart=job)
            if not response:
                logging.error(response.message)
            else:
                logging.info(response.message)
        self.model.load()

    def on_abort(self, jobs):
        for job in jobs:
            response = api.jobs(abort=job)
            if not response:
                logging.error(response.message)
            else:
                logging.info(response.message)
            self.model.load()
