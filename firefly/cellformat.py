__all__ = ["FireflyObject"]

from nxtools import s2time, s2tc

from firefly.common import Colors

from firefly.core.common import config
from firefly.core.base_objects import BaseObject
from firefly.core.enum import ObjectStatus, RunMode


RUNDOWN_EVENT_BACKGROUND_COLOR = "#0f0f0f"

STATUS_FG_COLORS = {
    ObjectStatus.OFFLINE: Colors.TEXT_RED,
    ObjectStatus.ONLINE: Colors.TEXT_NORMAL,
    ObjectStatus.CREATING: Colors.TEXT_YELLOW,
    ObjectStatus.TRASHED: Colors.TEXT_FADED,
    ObjectStatus.ARCHIVED: Colors.TEXT_FADED,
    ObjectStatus.RESET: Colors.TEXT_YELLOW,
    ObjectStatus.REMOTE: Colors.TEXT_YELLOW,
    ObjectStatus.UNKNOWN: Colors.TEXT_RED,
    ObjectStatus.CORRUPTED: Colors.TEXT_RED,
    ObjectStatus.AIRED: Colors.TEXT_FADED2,
    ObjectStatus.ONAIR: Colors.TEXT_RED,
    ObjectStatus.RETRIEVING: Colors.TEXT_YELLOW,
}

DEFAULT_FOLDER = {"color": 0xAAAAAA, "title": "-"}


class CellFormat(object):
    key = "none"

    def display(self, obj, **kwargs):
        return None

    def foreground(self, obj, **kwargs):
        return None

    def background(self, obj, **kwargs):
        return None

    def decoration(self, obj, **kwargs):
        return None

    def font(self, obj, **kwargs):
        return None

    def tooltip(self, obj, **kwargs):
        return None


#
# Cell formatters
#


class FormatFolder(CellFormat):
    key = "id_folder"

    def display(self, obj, **kwargs):
        id_folder = obj["id_folder"]
        return config["folders"].get(id_folder, DEFAULT_FOLDER)["title"]

    def foreground(self, obj, **kwargs):
        id_folder = obj["id_folder"]
        return config["folders"].get(id_folder, DEFAULT_FOLDER)["color"]


class FormatContentType(CellFormat):
    key = "content_type"

    def decoration(self, obj, **kwargs):
        return ["text", "video", "audio", "image"][int(obj[self.key])]


class FormatPromoted(CellFormat):
    key = "promoted"

    def display(self, obj, **kwargs):
        return ""

    def decoration(self, obj, **kwargs):
        return ["unstar", "star"][int(obj[self.key])]


def parse_item_status(obj):
    asset = obj.asset
    try:
        obj.id_channel
    except Exception:
        return ObjectStatus.UNKNOWN
    pskey = f"playout_status/{obj.id_channel}"

    if asset["status"] == ObjectStatus.OFFLINE:
        return ObjectStatus.OFFLINE

    if pskey not in asset.meta:
        return ObjectStatus.REMOTE
    elif asset[pskey]["status"] == ObjectStatus.OFFLINE:
        return ObjectStatus.REMOTE
    elif asset[pskey]["status"] == ObjectStatus.ONLINE:
        return ObjectStatus.ONLINE
    elif asset[pskey]["status"] == ObjectStatus.CORRUPTED:
        return ObjectStatus.CORRUPTED
    elif asset[pskey]["status"] == ObjectStatus.CREATING:
        return ObjectStatus.CREATING

    return ObjectStatus.UNKNOWN


class FormatStatus(CellFormat):
    key = "status"

    def display(self, obj, **kwargs):
        if obj.object_type == "asset":
            return obj.show("status")

        if obj.object_type != "item" or not obj["id_asset"]:
            return ""

        state = parse_item_status(obj)

        xfr = ""
        xfrp = obj["transfer_progress"]
        if xfrp:
            if xfrp == -1:
                xfr = " (PENDING)"
            elif xfrp == 0:
                xfr = " (STARTING)"
            elif xfrp < 100:
                xfr = f" ({xfrp:.01f}%)"

        return ObjectStatus(state).name + xfr

    def foreground(self, obj, **kwargs):
        if obj.object_type == "asset":
            return STATUS_FG_COLORS[obj["status"]]

        elif obj.object_type == "item" and obj["id_asset"]:
            return STATUS_FG_COLORS[parse_item_status(obj)]


class FormatRundownDifference(CellFormat):
    key = "rundown_difference"

    def display(self, obj, **kwargs):
        if obj[self.key]:
            if obj["run_mode"] == RunMode.RUN_SKIP:
                return ""
            return s2tc(abs(obj[self.key]))
        return ""

    def foreground(self, obj, **kwargs):
        if obj["rundown_broadcast"] and obj["rundown_scheduled"]:
            diff = obj["rundown_broadcast"] - obj["rundown_scheduled"]
            return ["#ff0000", "#00ff00"][diff >= 0]


class FormatRundownScheduled(CellFormat):
    key = "rundown_scheduled"

    def display(self, obj, **kwargs):
        if obj.id:
            if obj["run_mode"] == RunMode.RUN_SKIP:
                return ""
            return obj.show(self.key)
        return ""


class FormatRundownBroadcast(CellFormat):
    key = "rundown_broadcast"

    def display(self, obj, **kwargs):
        if obj.id:
            if obj["run_mode"] == RunMode.RUN_SKIP:
                return ""
            return obj.show(self.key)
        return ""


class FormatRunMode(CellFormat):
    key = "run_mode"

    def display(self, obj, **kwargs):
        if obj[self.key] == RunMode.RUN_MANUAL:
            return "MANUAL"
        if obj[self.key] == RunMode.RUN_SOFT:
            return "SOFT"
        elif obj[self.key] == RunMode.RUN_HARD:
            return "HARD"
        elif obj[self.key] == RunMode.RUN_SKIP:
            return "SKIP"
        if obj.id:
            return "AUTO"
        return ""


class FormatDuration(CellFormat):
    key = "duration"

    def display(self, obj, **kwargs):
        if obj.get("loop"):
            return "--:--:--:--"
        if obj.object_type in ["asset", "item"] and obj["duration"]:
            t = s2time(obj.duration)
            if obj.object_type == "asset" and obj["subclips"]:
                t += "*"
            return t
        else:
            return ""

    def foreground(self, obj, **kwargs):
        if obj["loop"]:
            return Colors.TEXT_YELLOW
        if obj["mark_in"] or obj["mark_out"]:
            return "#00ccaa"

    def tooltip(self, obj, **kwargs):
        if not (obj["mark_in"] or obj["mark_out"] or obj["subclips"]):
            return None

        res = "Original duration: {}\n\nIN: {}\nOUT: {}".format(
            obj.show("duration"), obj.show("mark_in"), obj.show("mark_out")
        )
        if obj["subclips"]:
            res += "\n\n{} subclips".format(len(obj["subclips"]))
        return res


class FormatMarkIn(CellFormat):
    key = "mark_in"

    def display(self, obj, **kwargs):
        if obj[self.key]:
            return obj.show(self.key)
        return ""


class FormatMarkOut(CellFormat):
    key = "mark_out"

    def display(self, obj, **kwargs):
        if obj[self.key]:
            return obj.show(self.key)
        return ""


class FormatState(CellFormat):
    key = "qc/state"

    def display(self, obj, **kwargs):
        return ""

    def decoration(self, obj, **kwargs):
        return {
            0: "qc_new",
            1: "qc_failed",
            2: "qc_passed",
            3: "qc_rejected",
            4: "qc_approved",
        }[int(obj.meta.get(self.key, 0))]

    def foreground(self, obj, **kwargs):
        return {0: None, 1: "#cc0000", 2: "#cccc00", 3: "#cc0000", 4: "#00cc00"}[
            int(obj.meta.get(self.key, 0))
        ]

    def tooltip(self, obj, **kwargs):
        if "qc/report" in obj.meta:
            return obj["qc/report"]


class FormatTitle(CellFormat):
    key = "title"

    def decoration(self, obj, **kwargs):
        if obj.object_type == "event":
            return ["unstar-sm", "star-sm"][int(obj["promoted"])]
        elif obj["status"] == ObjectStatus.ARCHIVED:
            return "archive-sm"
        elif obj["status"] == ObjectStatus.TRASHED:
            return "trash-sm"

        if obj.object_type == "item":
            if obj["id_folder"]:
                return "folder_" + str(obj["id_folder"])
            elif obj["item_role"] == "lead_in":
                return "lead-in-sm"
            elif obj["item_role"] == "lead_out":
                return "lead-out-sm"
            elif obj["item_role"] == "live":
                return "live-sm"
            elif obj["item_role"] == "placeholder":
                return "placeholder-sm"

    # REMOVED: use state-based colors in status coulmn only
    def foreground(self, obj, **kwargs):
        if obj.object_type == "asset":
            return STATUS_FG_COLORS[obj["status"]]
        elif obj.object_type == "item" and obj["id_asset"]:
            item_status = parse_item_status(obj)
            if item_status == ObjectStatus.REMOTE:
                return STATUS_FG_COLORS[ObjectStatus.ONLINE]
            return STATUS_FG_COLORS[item_status]

    def font(self, obj, **kwargs):
        if obj.object_type == "event":
            return "bold"


format_helpers_list = [
    FormatFolder,
    FormatContentType,
    FormatPromoted,
    FormatStatus,
    FormatRundownDifference,
    FormatRundownScheduled,
    FormatRundownBroadcast,
    FormatRunMode,
    FormatState,
    FormatTitle,
    FormatDuration,
    FormatMarkIn,
    FormatMarkOut,
]

format_helpers = {}
for h in format_helpers_list:
    helper = h()
    format_helpers[h.key] = helper

#
# Firefly object
#


class FireflyObject(BaseObject):
    def format_display(self, key, **kwargs):
        if key in format_helpers:
            val = format_helpers[key].display(self, **kwargs)
            if val is not None:
                return val
        return self.show(key, hide_null=True, shorten=100)

    def format_foreground(self, key, **kwargs):
        model = kwargs.get("model")
        if self.object_type == "item":
            if (
                self["status"] == ObjectStatus.AIRED
                and model
                and model.cued_item != self.id
                and model.current_item != self.id
            ):
                return STATUS_FG_COLORS[ObjectStatus.AIRED]
            if self["run_mode"] == RunMode.RUN_SKIP:
                return Colors.TEXT_FADED
        if key in format_helpers:
            return format_helpers[key].foreground(self, **kwargs)

    def format_background(self, key, **kwargs):
        model = kwargs.get("model")
        if self.object_type == "event":
            if model.__class__.__name__ == "RundownModel":
                return RUNDOWN_EVENT_BACKGROUND_COLOR
        if model and self.object_type == "item":
            if not self.id:
                return "#111140"
            if model.cued_item == self.id:
                return "#059005"
            elif model.current_item == self.id:
                return "#900505"
            elif self.object_type == "item" and self["item_role"] == "live":
                return Colors.LIVE_BACKGROUND
            elif not self["id_asset"]:
                return "#303030"
        return None

    def format_decoration(self, key, **kwargs):
        if key in format_helpers:
            return format_helpers[key].decoration(self, **kwargs)
        return None

    def format_font(self, key, **kwargs):
        if self.object_type == "item":
            if self["run_mode"] == RunMode.RUN_SKIP and key == "title":
                return "strikeout"
            if self["id_asset"] == self["rundown_event_asset"]:
                return "bold"
        if key in format_helpers:
            return format_helpers[key].font(self, **kwargs)

    def format_tooltip(self, key, **kwargs):
        if key in format_helpers:
            return format_helpers[key].tooltip(self, **kwargs)
