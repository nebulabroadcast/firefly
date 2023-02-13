from typing import TYPE_CHECKING, Any

from nxtools import format_filesize, format_time, s2tc

from firefly.enum import ContentType, MediaType, ObjectStatus, QCState
from firefly import settings

if TYPE_CHECKING:
    from firefly.objects.base import BaseObject
    from firefly.settings.metatypes import MetaType


def format_cs_values(metatype: "MetaType", values: list[str]) -> str:
    if metatype.cs is None:
        return ",".join(values)
    return ", ".join([metatype.csdata.title(value) for value in values])



def format_meta(
    parent, object: "BaseObject", key: str, **kwargs: dict[str, Any],
) -> str:
    """Return a human-readable string representation of a metadata value."""

    if not (value := object.get(key)):
        return ""

    match key:
        case "title" | "subtitle" | "description":
            return value  # Most common, so test it first
        case "content_type":
            return ContentType(int(value)).name
        case "media_type":
            return MediaType(int(value)).name
        case "status":
            return ObjectStatus(int(value)).name
        case "qc/state":
            return QCState(int(value)).name
        case "duration":
            return s2tc(value)
        case "file/size":
            return format_filesize(value)
        case "id_folder":
            if not (folder := settings.get_folder(value)):
                return "UNKNOWN"
            return folder.name

    meta_type = parent[key]

    match meta_type.type:
        case "string" | "text":
            return str(value)
        case "integer":
            return str(value)
        case "numeric":
            return str(round(value, 3))
        case "boolean":
            return "yes" if value else "no"
        case "datetime":
            return format_time(
                value,
                time_format=meta_type.format or "%Y-%m-%d %H:%M:%S",
            )
        case "timecode":
            return s2tc(value)
        case "select":
            return format_cs_values(meta_type, [value])
        case "list":
            return format_cs_values(meta_type, value)
        case "color":
            return f"#{value:06x}"

    return str(value)
