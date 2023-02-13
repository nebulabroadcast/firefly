import time
import pprint

from nxtools import logging

from firefly.enum import RunMode, ObjectStatus, Colors
from firefly.metadata import MetaTypes
from firefly.metadata.normalize import normalize_meta
from firefly.metadata.format import format_meta

from .format import format_helpers, STATUS_FG_COLORS


class BaseObject:
    """Base object properties."""

    required = []
    defaults = {}

    def __init__(self, id=False, **kwargs):
        """Object constructor."""
        self.text_changed = self.meta_changed = False
        self.is_new = True
        self.meta = {}
        meta = kwargs.get("meta", {})
        if id:
            assert type(id) == int, f"{self.object_type} ID must be integer"
        assert (
            meta is not None
        ), f"Unable to load {self.object_type}. Meta must not be 'None'"
        assert hasattr(meta, "keys"), "Incorrect meta!"
        for key in meta:
            self.meta[key] = meta[key]
        if "id" in self.meta:
            self.is_new = False
        elif not self.meta:
            if id:
                self.load(id)
                self.is_new = False
            else:
                self.new()
                self.is_new = True
                self["ctime"] = self["mtime"] = time.time()
        for key in self.defaults:
            if key not in self.meta:
                self.meta[key] = self.defaults[key]

    @property
    def id(self):
        """Return object ID."""
        return self.meta.get("id", None)

    @property
    def id_folder(self):
        """Return folder ID."""
        return self.meta.get("id_folder")

    @property
    def meta_types(self):
        """Return meta types.

        If the object has a folder, use the per-folder metadata overrides.
        This allows things filters and defaults to be overridden per-folder.
        """
        return MetaTypes(self.id_folder)

    @property
    def object_type(self):
        return self.__class__.__name__.lower()

    def keys(self):
        """Return list of metadata keys."""
        return self.meta.keys()

    def get(self, key, default=False):
        """Return a metadata value."""
        if key in self.meta:
            return self[key]
        return default

    def __getitem__(self, key):
        key = key.lower().strip()
        if key == "_duration":
            return self.duration  # noqa
        if key not in self.meta_types:
            return self.meta.get(key, None)
        else:
            return self.meta.get(key, self.meta_types[key].default)

    def __setitem__(self, key, value):
        """Set a metadata value

        Raises ValueError if the provided value is cannot
        be casted to the expected type.
        """
        try:
            value = normalize_meta(self.meta_types, key, value)
        except ValueError as e:
            raise ValueError(f"Invalid value for {key}: {value}") from e
        if value is None:
            self.meta.pop(key, None)
        else:
            self.meta[key] = value

        self.meta_changed = True
        if key in self.meta_types:
            if self.meta_types[key].fulltext:
                self.text_changed = True

    def update(self, data):
        for key in data.keys():
            self[key] = data[key]

    def new(self):
        pass

    def load(self, id):
        pass

    def save(self, **kwargs):
        if not kwargs.get("silent", False):
            logging.debug(f"Saving {self}")
        self["ctime"] = self["ctime"] or time.time()
        if kwargs.get("set_mtime", True):
            self["mtime"] = time.time()
        for key in self.required:
            if (key not in self.meta) and (key in self.defaults):
                self[key] = self.defaults[key]
            assert key in self.meta, f"Unable to save {self}. {key} is required"

    def delete(self, **kwargs):
        assert self.id > 0, "Unable to delete unsaved object"

    def __delitem__(self, key):
        key = key.lower().strip()
        if key not in self.meta:
            return
        del self.meta[key]

    def __repr__(self):
        if self.id:
            result = f"{self.object_type} ID:{self.id}"
        else:
            result = f"new {self.object_type}"
        if self.object_type == "item" and not hasattr(self, "_asset"):
            title = ""
        else:
            title = self["title"]
        if title:
            result += f" ({title})"
        return result

    def __len__(self):
        return not self.is_new

    def show(self, key, **kwargs):
        return format_meta(self.meta_types, self, key, **kwargs)

    def show_meta(self):
        return pprint.pformat(self.meta)

    #
    # Cell format
    #

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
                return "#000000"
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
            if self.get("id_asset") == self.get("rundown_event_asset"):
                return "bold"
        if key in format_helpers:
            return format_helpers[key].font(self, **kwargs)

    def format_tooltip(self, key, **kwargs):
        if key in format_helpers:
            return format_helpers[key].tooltip(self, **kwargs)
