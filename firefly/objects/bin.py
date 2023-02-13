from .base import BaseObject


class Bin(BaseObject):
    object_type_id = 2
    required = ["bin_type"]
    defaults = {"bin_type": 0}

    @property
    def duration(self):
        if "duration" not in self.meta:
            duration = 0
            for item in self.items:
                duration += item.duration
            self["duration"] = duration
        return self["duration"]
