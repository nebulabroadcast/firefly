from firefly.common import *
from firefly.widgets import *
from firefly.view import *

__all__ = ["FireflyJobsView"]

DEFAULT_HEADER_DATA = [
        "id",
        "title",
        "action",
        "ctime",
        "stime",
        "etime",
        "progress",
    ]

def job_format(data, key):
    if key in ["ctime", "stime", "etime"]:
        return format_time(data[key])
    elif key == "title":
        return asset_cache[data["id_asset"]]["title"]
    elif key == "action":
        return config["actions"][data["id_action"]]["title"]
    elif key == "service":
        #TODO
 #       return config["action"][data["id_action"]]["title"]
        return data["id_service"]
    elif key == "message":
        return data["message"]
    elif key == "id":
        return str(data["id"])
    elif key == "progress":
        if data["status"] == 1:
            return "{:.02f}%".format(data["progress"])
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
        "title" : 300,
        "action" : 80,
        "service" : 80,
        "ctime" : 150,
        "stime" : 150,
        "etime" : 150,
        "progress" : 150,
    }

colors = {
        PENDING     : QColor("#cccccc"),
        IN_PROGRESS : QColor("#ffffff"),
        COMPLETED   : QColor("#109410"),
        FAILED      : QColor("#941010"),
        ABORTED     : QColor("#646464"),
        RESTART     : QColor("#cccccc"),
        SKIPPED     : QColor("#646464"),
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
            return "{}\n\n{}".format(obj["message"], asset_cache[obj["id_asset"]])
        elif role == Qt.ForegroundRole:
            return colors[obj["status"]]

        return None


    def load(self, **kwargs):
        self.request_data.update(kwargs)
        start_time = time.time()
        self.beginResetModel()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.object_data = []
        result = api.jobs(**self.request_data)
        if result.is_error:
            logging.error(result.message)
        else:
            request_assets = []
            for row in result.data:
                self.object_data.append(row)
                request_assets.append([row["id_asset"], 0])
            asset_cache.request(request_assets)
        self.endResetModel()
        QApplication.restoreOverrideCursor()


class FireflyJobsView(FireflyView):
    def __init__(self, parent):
        super(FireflyJobsView, self).__init__(parent)
        self.setSortingEnabled(True)
        self.model = JobsModel(self)
        self.model.header_data = DEFAULT_HEADER_DATA
        self.sort_model = FireflySortModel(self.model)
        self.setModel(self.sort_model)
        for i, h in enumerate(self.model.header_data):
            if h in colw :
                self.horizontalHeader().resizeSection(i, colw[h])
