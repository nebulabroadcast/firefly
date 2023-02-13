from .base import BaseObject
from .asset import asset_cache

class Item(BaseObject):
    object_type_id = 1
    required = ["id_bin", "id_asset", "position"]

    def __getitem__(self, key):
        key = key.lower().strip()
        if key not in self.meta:
            if key == "id_asset":
                return 0
            elif self.asset:
                return self.asset[key]
            else:
                return self.meta_types[key].default
        return self.meta[key]

    @property
    def asset(self):
        if not self["id_asset"]:
            return False
        return asset_cache.get(self["id_asset"])

    @property
    def id_folder(self):
        if self.asset:
            return self.asset.id_folder
        return self.meta.get("id_folder")

    def mark_in(self, new_val=False):
        if new_val:
            self["mark_in"] = new_val
        return max(float(self["mark_in"] or 0), 0)

    def mark_out(self, new_val=False):
        if new_val:
            self["mark_out"] = new_val
        return max(float(self["mark_out"] or 0), 0)

    @property
    def duration(self):
        """Final duration of the item"""
        if self["id_asset"]:
            dur = self.asset["duration"] or 0
        elif self["duration"]:
            dur = self["duration"] or 0
        else:
            return self.mark_out() - self.mark_in()
        if not dur:
            return 0
        mark_in = self.mark_in()
        mark_out = self.mark_out()
        if mark_out > 0:
            dur = mark_out + (1 / self.fps)
        if mark_in > 0:
            dur -= mark_in
        return dur

    @property
    def fps(self):
        return self.asset.fps

    @property
    def file_path(self):
        if not self["id_asset"]:
            return ""
        return self.asset.file_path

