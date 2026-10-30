from .base import BaseObject


class Bin(BaseObject):
    object_type_id = 2
    required = ["bin_type"]
    defaults = {"bin_type": 0}

    @property
    def duration(self):
        return self.meta.get("duration", 0)
