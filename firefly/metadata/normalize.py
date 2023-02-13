from firefly import settings
from typing import Any

ALWAYS_TO_INT = [
    "id_folder",
    "id_asset",
    "id_bin",
    "id_event",
    "id_magic",
    "id_channel",
    "content_type",
    "media_type",
    "status",
    "ctime",
    "mtime",
    "position",
    "start",
    "stop",
]


def is_serializable(value: Any) -> bool:
    """Check if a value is serializable.

    This is used to check if a value can be stored in the database.
    """
    if type(value) in (str, int, float, bool, dict, list, tuple):
        return True
    return False


def parse_bool(value: Any) -> bool:
    if isinstance(value, str):
        if value.lower() in ("yes", "true", "1"):
            return True
        if value.lower() in ("no", "false", "0", 0, False):
            return False
    return bool(value)


def normalize_meta(parent, key: str, value: Any) -> Any:
    """Ensure that metadata is in the correct format.

    Returns the correct value for the given key.
    Raises a ValueError if the value cannot be converted.
    """

    # Some keys we need to enforce really hard
    if key in ALWAYS_TO_INT:
        return int(value or 0)

    # If there's no matching metatype, just return the value
    if key not in settings.metatypes.keys():
        if not is_serializable(value):
            raise ValueError(f"Value {value} of undefined key {key} is not supported.")
        return value

    meta_type = parent[key]

    if value == meta_type.default:
        return value

    match meta_type.type:
        case "string" | "text":
            return str(value)

        case "integer":
            return int(value or 0)

        case "boolean":
            return parse_bool(value)

        case "datetime" | "timecode" | "numeric":
            return float(value)

        case "object":
            assert is_serializable(value)
            return value

        case "fraction":
            assert type(value) is str
            return value

        case "select":
            assert type(value) is str
            return str(value)

        case "list":
            if not value:
                return []
            if not isinstance(value, list):
                raise ValueError("List is already a list")
            return [str(v) for v in value]

        case "color":
            if isinstance(value, str):
                if value.startswith("#"):
                    value = value[1:]
                return int(value, 16)
            return int(value)

        case _:
            return value
