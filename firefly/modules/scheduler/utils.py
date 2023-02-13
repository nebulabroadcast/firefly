import re

from nxtools import format_time

from firefly.metadata import meta_types
from firefly.qt import QFontMetrics


def suggested_duration(dur):
    adur = int(dur) + 360
    g = adur % 300
    return adur - g + 300 if g > 150 else adur - g


def text_shorten(text, font, target_width):
    fm = QFontMetrics(font)
    exps = [r"\W|_", r"[a-z]([aáeéěiíoóuůú])", r"[a-z]", r"."]
    r = exps.pop(0)
    text = text[::-1]
    while fm.boundingRect(text).width() > target_width:
        text, n = re.subn(r, "", text, 1)
        if n == 0:
            r = exps.pop(0)
    return text[::-1]


def dump_template(calendar):
    result = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n"""
    result += "<template>\n"

    DAY_NAMES = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    days = [[], [], [], [], [], [], []]
    for event in calendar.events:
        week_offset = event["start"] - calendar.week_start_time
        day = int(week_offset / (3600 * 24))
        if day < 0 or day > 6:
            continue
        days[day].append(event)

    for i, day in enumerate(days):
        result += f"    <!-- {DAY_NAMES[i]} -->\n"
        result += "    <day>\n"
        for event in day:
            clock = format_time(event["start"], "%H:%M")
            result += f"        <event time=\"{clock}\"> <!-- {event['title']} -->\n"
            for key in event.meta:
                if meta_types[key]["ns"] != "m":
                    continue
                value = event[key]
                if type(value) is str:
                    value = value.replace("&", "&amp;")
                result += f'            <meta key="{key}">{value}</meta>\n'
            result += "        </event>\n"
        result += "    </day>\n"

    result += "</template>"
    return result



def export_template(scheduler):
    pass
    # data = dump_template(scheduler.calendar)
    # try:
    #     if not os.path.exists("templates"):
    #         os.makedirs("templates")
    # except Exception:
    #     log_traceback()
    # save_file_path = QFileDialog.getSaveFileName(
    #     self,
    #     "Save scheduler template",
    #     os.path.abspath("templates"),
    #     "Templates (*.xml)",
    # )[0]
    # if os.path.splitext(save_file_path)[1].lower() != ".xml":
    #     save_file_path += ".xml"
    # try:
    #     with open(save_file_path, "wb") as save_file:
    #         save_file.write(data.encode("utf-8"))
    # except Exception:
    #     log_traceback()


def import_template(scheduler, day_offset=0):
    pass
    # try:
    #     if not os.path.exists("templates"):
    #         os.makedirs("templates")
    # except Exception:
    #     log_traceback()
    # file_path = QFileDialog.getOpenFileName(
    #     self, "Open template", os.path.abspath("templates"), "Templates (*.xml)"
    # )[0]
    #
    # if not file_path:
    #     return
    #
    # QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    # try:
    #     feed = open(file_path, "rb").read().decode("utf-8")
    #     data = xml(feed)
    # except Exception:
    #     QApplication.restoreOverrideCursor()
    #     log_traceback()
    #     return
    # ch, cm = self.calendar.day_start
    # events = []
    # try:
    #     for day_index, day in enumerate(data.findall("day")):
    #         day_start = self.calendar.week_start_time + (3600 * 24 * day_index)
    #         for event_data in day.findall("event"):
    #             hh, mm = [int(x) for x in event_data.attrib["time"].split(":")]
    #
    #             clock_offset = (hh * 3600) + (mm * 60) - (ch * 3600) - (cm * 60)
    #             if (hh * 3600) + (mm * 60) < (ch * 3600) - (cm * 60):
    #                 clock_offset += 24 * 3600
    #
    #             start_time = day_start + clock_offset + (day_offset * 3600 * 24)
    #
    #             event = Event(meta={"start": start_time})
    #             for m in event_data.findall("meta"):
    #                 key = m.attrib["key"]
    #                 value = m.text
    #                 if value:
    #                     event[key] = value
    #
    #             items_data = event_data.find("items")
    #             if items_data is not None:
    #                 event.meta["_items"] = []
    #                 for ipos, item_data in enumerate(items_data.findall("item")):
    #                     item = Item()
    #                     item["position"] = ipos + 1
    #                     for kv in item_data.findall("meta"):
    #                         item[kv.attrib["key"]] = kv.text
    #                     event.meta["_items"].append(item.meta)
    #
    #             events.append(event.meta)
    #         if day_offset:  # Importing single day.
    #             break
    # except Exception:
    #     QApplication.restoreOverrideCursor()
    #     log_traceback("Unable to parse template:")
    #     return
    # if not events:
    #     QApplication.restoreOverrideCursor()
    #     return
    # response = api.scheduler(channel=self.id_channel, events=events)
    # QApplication.restoreOverrideCursor()
    # if not response:
    #     logging.error(response.message)
    # else:
    #     logging.info(response.message)
    # self.load()
