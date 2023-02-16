import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from firefly.settings import AcceptModel
    from firefly.objects import Asset


def date_offset(date: str, offset: int) -> tuple[str, int]:
    """Returns date and week number for given date and offset."""
    parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    offset_delta = datetime.timedelta(days=offset)
    new_date = parsed_date + offset_delta
    week_number = new_date.isocalendar()[1]
    return new_date.strftime("%Y-%m-%d"), week_number


# TODO: do we need day start? it is used only to get initial
# state of scheduler.
def get_this_monday(day_start: tuple[int, int] | None = None) -> tuple[str, int]:
    """Returns date and week number for this monday."""
    today = datetime.datetime.today()
    day_of_week = today.isoweekday()
    days_to_subtract = day_of_week - 1
    first_day = today - datetime.timedelta(days=days_to_subtract)
    week_number = first_day.isocalendar()[1]
    return first_day.strftime("%Y-%m-%d"), week_number


def can_append(asset: "Asset", conditions: "AcceptModel") -> bool:
    if conditions.folders:
        if asset["id_folder"] not in conditions.folders:
            return False
    if conditions.media_types:
        if asset["media_type"] not in conditions.media_types:
            return False
    if conditions.content_types:
        if asset["content_type"] not in conditions.content_types:
            return False
    return True
