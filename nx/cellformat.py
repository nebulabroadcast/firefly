from .common import *

from nebulacore import *
from nebulacore.base_objects import BaseObject

__all__ = ["FireflyObject"]

RUNDOWN_EVENT_BACKGROUND_COLOR = "#0f0f0f"

STATUS_FG_COLORS = {
    OFFLINE  : COLOR_TEXT_RED,
    ONLINE   : COLOR_TEXT_NORMAL,
    CREATING : COLOR_TEXT_YELLOW,
    TRASHED  : COLOR_TEXT_FADED,
    ARCHIVED : COLOR_TEXT_FADED,
    RESET    : COLOR_TEXT_YELLOW,
    REMOTE   : COLOR_TEXT_YELLOW,
    UNKNOWN  : COLOR_TEXT_RED,
    CORRUPTED  : COLOR_TEXT_RED,
    AIRED    : COLOR_TEXT_FADED2,
    ONAIR    : COLOR_TEXT_RED,
    RETRIEVING  : COLOR_TEXT_YELLOW
}

DEFAULT_FOLDER = {
        "color" : 0xaaaaaa,
        "title" : "-"
    }

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
    except:
        print ("bad idc", obj.meta)
    pskey = "playout_status/{}".format(obj.id_channel)

    if asset["status"] == OFFLINE:
        return OFFLINE

    if not pskey in asset.meta:
        return  REMOTE
    elif asset[pskey]["status"] == OFFLINE:
        return REMOTE
    elif asset[pskey]["status"] == ONLINE:
        return  ONLINE
    elif asset[pskey]["status"] == CORRUPTED:
        return CORRUPTED
    elif asset[pskey]["status"] == CREATING:
        return CREATING

    return UNKNOWN


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
                xfr = " ({:.01f}%)".format(xfrp)

        return get_object_state_name(state).upper() + xfr

    def foreground(self, obj, **kwargs):
        if obj.object_type == "asset":
            return STATUS_FG_COLORS[obj["status"]]

        elif obj.object_type == "item" and obj["id_asset"]:
            return STATUS_FG_COLORS[parse_item_status(obj)]




class FormatRundownDifference(CellFormat):
    key = "rundown_difference"
    def display(self, obj, **kwargs):
        if obj[self.key]:
            if obj["run_mode"] == RUN_SKIP:
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
            if obj["run_mode"] == RUN_SKIP:
                return ""
            return obj.show(self.key)
        return ""

class FormatRundownBroadcast(CellFormat):
    key = "rundown_broadcast"
    def display(self, obj, **kwargs):
        if obj.id:
            if obj["run_mode"] == RUN_SKIP:
                return ""
            return obj.show(self.key)
        return ""


class FormatRunMode(CellFormat):
    key = "run_mode"
    def display(self, obj, **kwargs):
        if obj[self.key] == RUN_MANUAL:
            return "MANUAL"
        if obj[self.key] == RUN_SOFT:
            return "SOFT"
        elif obj[self.key] == RUN_HARD:
            return "HARD"
        elif obj[self.key] == RUN_SKIP:
            return "SKIP"
        if obj.id:
            return "AUTO"
        return ""

class FormatDuration(CellFormat):
    key = "duration"
    def display(self, obj, **kwargs):
        if obj["loop"]:
            return "--:--:--:--"
        if obj.object_type in ["asset", "item"] and obj["duration"]:
            t = s2time(obj.duration)
            if obj.object_type == "asset" and obj["subclips"]:
                t+="*"
            return t
        else:
            return ""

    def foreground(self, obj, **kwargs):
        if obj["loop"]:
            return COLOR_TEXT_YELLOW
        if obj["mark_in"] or obj["mark_out"]:
            return "#00ccaa"

    def tooltip(self, obj, **kwargs):
        if not (obj["mark_in"] or obj["mark_out"] or obj["subclips"]):
            return None

        res = "Original duration: {}\n\nIN: {}\nOUT: {}".format(obj.show("duration"), obj.show("mark_in"), obj.show("mark_out"))
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
                0 : "qc_new",
                1 : "qc_failed",
                2 : "qc_passed",
                3 : "qc_rejected",
                4 : "qc_approved"
                }[int(obj.meta.get(self.key, 0))]

    def foreground(self, obj, **kwargs):
        return {
                0 : None,
                1 : "#cc0000",
                2 : "#cccc00",
                3 : "#cc0000",
                4 : "#00cc00"
                }[int(obj.meta.get(self.key, 0))]

    def tooltip(self, obj, **kwargs):
        if "qc/report" in obj.meta:
            return obj["qc/report"]


class FormatTitle(CellFormat):
    key = "title"
    def decoration(self, obj, **kwargs):
        if obj.object_type == "event":
            return ["unstar-sm", "star-sm"][int(obj["promoted"])]
        elif obj["status"] == ARCHIVED:
            return "archive-sm"
        elif obj["status"] == TRASHED:
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

    def foreground(self, obj, **kwargs):
        if obj.object_type == "asset":
            return STATUS_FG_COLORS[obj["status"]]
        elif obj.object_type == "item" and obj["id_asset"]:
            return STATUS_FG_COLORS[parse_item_status(obj)]

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
        return self.show(
                key,
                hide_null=True,
                shorten=100
            )

    def format_foreground(self, key, **kwargs):
        if self.object_type == "item":
            if self["status"] == AIRED:
                return STATUS_FG_COLORS[AIRED]
            if self["run_mode"] == RUN_SKIP:
                return COLOR_TEXT_FADED
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
            if self.object_type == "item" and self["item_role"] == "live":
                return COLOR_LIVE_BACKGROUND
            elif model.cued_item == self.id:
                return "#059005"
            elif model.current_item == self.id:
                return "#900505"
            elif not self["id_asset"]:
                return "#303030"
        return None

    def format_decoration(self, key, **kwargs):
        if key in format_helpers:
            return format_helpers[key].decoration(self, **kwargs)
        return None

    def format_font(self, key, **kwargs):
        if self.object_type == "item":
            if self["run_mode"] == RUN_SKIP and key == "title":
                return "strikeout"
            if self["id_asset"] == self["rundown_event_asset"]:
                return "bold"
        if key in format_helpers:
            return format_helpers[key].font(self, **kwargs)

    def format_tooltip(self, key, **kwargs):
        if key in format_helpers:
            return format_helpers[key].tooltip(self, **kwargs)
