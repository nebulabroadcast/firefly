import datetime
import time

from unidecode import unidecode


def format_time(
    timestamp: float | None = None,
    time_format: str = "%Y-%m-%d %H:%M:%S",
    never_placeholder: str = "never",
    gmt: bool = False,
) -> str:
    """Format a unix timestamp as local (or GMT) time"""
    if not timestamp:
        return never_placeholder
    tm = time.gmtime(timestamp) if gmt else time.localtime(timestamp)
    return time.strftime(time_format, tm)


def format_filesize(value: float | None) -> str:
    """Return a human readable size for a byte count"""
    if not value:
        return ""
    for unit in ["bytes", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:3.1f} {unit}"
        value /= 1024.0
    return f"{value:3.1f} PB"


def datestr2ts(datestr: str, hh: int = 0, mm: int = 0, ss: int = 0) -> int:
    """Convert a YYYY-MM-DD string (and optional time) to a local unix timestamp"""
    yy, mo, dd = (int(i) for i in datestr.split("-"))
    return int(time.mktime(datetime.datetime(yy, mo, dd, hh, mm, ss).timetuple()))


def unaccent(string: str) -> str:
    """Transliterate to ASCII (e.g. for sorting): 'Šťastný' -> 'Stastny'"""
    return unidecode(string)
