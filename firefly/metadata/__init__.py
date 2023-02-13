import copy
import functools

from collections import defaultdict
from typing import Any
from pydantic import BaseModel
from nxtools import unaccent

import firefly

from .utils import filter_match, CachedObject


TYPE_DEFAULTS = {
    -1: None,
    "string": "",
    "text": "",
    "integer": 0,
    "numeric": 0,
    "boolean": False,
    "datetime": 0,
    "timecode": 0,
    "object": [],
    "fraction": "1/1",
    "select": "",
    "list": [],
    "color": 0x006FD5,
}


class ClassificationScheme(metaclass=CachedObject):
    def __init__(self, urn, filter=None):
        self.urn = urn
        self.csdata = dict(firefly.settings.cs.get(urn, []))
        if filter is not None:
            print("Filter", filter)
            self.valid_keys = [r for r in self.csdata if filter_match(filter, r)]
        else:
            self.valid_keys = list(self.csdata.keys())

    def __getitem__(self, value):
        return self.csdata.get(value, {})

    def __repr__(self):
        return f"<ClassificationScheme: {self.urn} ({len(self.valid_keys)} items)>"

    def title(self, value):
        return self[value].get("title", value)

    def description(self, value):
        return self[value].get("description", value)

    def role(self, value):
        return self[value].get("role", "option")


class MetaType(BaseModel):
    name: str
    ns: str = "m"
    type: str = "string"
    title: str = "Unknown"
    header: str | None = None
    description: str | None = None
    fulltext: int = 0
    default: Any = None
    cs: str | None = None
    mode: str | None = None
    format: str | None = None
    order: str | None = None
    filter: str | None = None

    # @functools.cached_property
    @property
    def csdata(self):
        cs = self.cs or "urn:special-nonexistent-cs"
        _filter = self.filter
        if type(_filter) == list:
            _filter = tuple(_filter)
        return ClassificationScheme(cs, _filter)

    # @functools.cached_property
    @property
    def cslist(self):
        if self.order is None:
            order = "value"
        else:
            order = self.order

        items = [
            {
                "value": value,
                "title": item.get("title", value),
                "description": item.get("description", ""),
                "role": item.get("role", "option"),
                "indent": len(value.split(".")),
            }
            for value, item in self.csdata.csdata.items()
            if value in self.csdata.valid_keys
        ]
        if order == "value":
            items.sort(key=lambda x: x["value"])
        elif order in ["title", "alias"]:
            items.sort(key=lambda x: unaccent(x["title"]))

        return items


def _folder_metaset(id_folder):
    return firefly.settings.get_folder(id_folder).fields


class MetaTypes(metaclass=CachedObject):
    def __init__(self, id_folder=None):
        self.id_folder = id_folder
        self._meta_types = None

    @property
    def meta_types(self):
        if not self._meta_types:
            self._meta_types = {}
            for name, mset in firefly.settings.metatypes.items():
                mt = MetaType(name=name, **mset)
                if mt.default is None:
                    mt.default = TYPE_DEFAULTS[mt.type]
                self._meta_types[name] = mt

            if self.id_folder:
                self._meta_types = copy.deepcopy(self._meta_types)
                for ffield in _folder_metaset(self.id_folder):
                    mt = self._meta_types[ffield.name]
                    for k, v in ffield.dict().items():
                        mt.__setattr__(k, v)
                    self._meta_types[ffield.name] = mt
        return self._meta_types

    def __contains__(self, name):
        return name in self.meta_types

    def __getitem__(self, key: str):
        return self.meta_types.get(key)

    def __iter__(self):
        return self.meta_types.__iter__()


meta_types = MetaTypes()


def clear_cs_cache():
    MetaTypes.clear_cache()
    ClassificationScheme.clear_cache()
