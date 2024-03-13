from .base import BaseObject


class Event(BaseObject):
    object_type_id = 3
    required = ["start", "id_channel"]

    @property
    def duration(self):
        return self.meta.get("duration", 0) or 0
