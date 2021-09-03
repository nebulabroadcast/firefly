from firefly.common import *
from firefly.widgets import *
from firefly.view import *

__all__ = ["FireflyJobsView"]

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
        return format_time(data[key], never_placeholder="")
    elif key == "title":
        return asset_cache[data["id_asset"]]["title"]
    elif key == "action":
        return config["actions"][data["id_action"]]["title"]
    elif key == "service":
        if data["id_service"]:
            id_service = data["id_service"]
            service = config["services"].get(id_service, None)
            if service:
                return f"{service['title']}@{service['host']}"
        return data["id_service"]
    elif key == "message":
        return data["message"]
    elif key == "id":
        return str(data["id"])
    elif key == "progress":
        if data["status"] == 1:
            return f"{data['progress']:.02f}%"
        else:
            return({
                    0 : "Pending",
                    1 : "In progress",
                    2 : "Completed",
                    3 : "Failed",
                    4 : "Aborted",
                    5 : "Restarted",
                    6 : "Skipped"
                }[data["status"]])
    return "-"


header_format = {
        "id" : "#",
        "title" : "Title",
        "action" : "Action",
        "service" : "Service",
        "ctime" : "Created",
        "stime" : "Started",
        "etime" : "Ended",
        "progress" : "Progress",
    }

colw = {
        "id" : 50,
        "title" : 200,
        "action" : 80,
        "service" : 160,
        "ctime" : 150,
        "stime" : 150,
        "etime" : 150,
        "progress" : 100,
    }

colors = {
        PENDING     : QColor(COLOR_TEXT_NORMAL),
        IN_PROGRESS : QColor(COLOR_TEXT_HIGHLIGHT),
        COMPLETED   : QColor(COLOR_TEXT_GREEN),
        FAILED      : QColor(COLOR_TEXT_RED),
        ABORTED     : QColor(COLOR_TEXT_RED),
        RESTART     : QColor(COLOR_TEXT_NORMAL),
        SKIPPED     : QColor(COLOR_TEXT_FADED),
    }


class JobsModel(FireflyViewModel):
    def __init__(self, *args, **kwargs):
        super(JobsModel, self).__init__(*args, **kwargs)
        self.request_data = {
                    "view" : "active"
                }
    def headerData(self, col, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return header_format[self.header_data[col]]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        obj = self.object_data[row]
        key = self.header_data[index.column()]

        if role == Qt.DisplayRole:
            return job_format(obj, key)
        elif role == Qt.ToolTipRole:
            return f"{obj['message']}\n\n{asset_cache[obj['id_asset']]}"
        elif role == Qt.ForegroundRole:
            return colors[obj["status"]]

        return None


    def load(self, **kwargs):
        self.request_data.update(kwargs)
        start_time = time.time()
        self.beginResetModel()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        data = []
        response = api.jobs(**self.request_data)
        if not response:
            logging.error(response.message)
        else:
            request_assets = []
            for row in response.data:
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
            if h in colw :
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
            if not i in used:
                used.append(i)
                result.append(self.model.object_data[i])
        return result

    def contextMenuEvent(self, event):
        jobs = [k["id"] for k in self.selected_jobs]
        if not jobs:
            return

        menu = QMenu(self)

        action_restart = QAction('Restart', self)
        action_restart.setStatusTip('Restart selected jobs')
        action_restart.triggered.connect(functools.partial(self.on_restart, jobs))
        menu.addAction(action_restart)

        action_abort = QAction('Abort', self)
        action_abort.setStatusTip('Abort selected jobs')
        action_abort.triggered.connect(functools.partial(self.on_abort, jobs))
        menu.addAction(action_abort)

        menu.exec_(event.globalPos())


    def on_restart(self, jobs):
        response = api.jobs(restart=jobs)
        if not response:
            logging.error(response.message)
        else:
            logging.info(response.message)
        self.model.load()


    def on_abort(self, jobs):
        response = api.jobs(abort=jobs)
        if not response:
            logging.error(response.message)
        else:
            logging.info(response.message)
        self.model.load()
