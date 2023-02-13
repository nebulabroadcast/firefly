from typing import Any


class FireflyUser:
    def __init__(self):
        self.meta = {}

    def __str__(self):
        return self.meta.get("login", "Anonymous")

    def __getitem__(self, key: str) -> Any:
        return self.meta.get(key)

    def update(self, meta: dict[str, Any]) -> None:
        self.meta.update(meta)

    @property
    def language(self):
        """Return the preferred language of the user."""
        return "cs"

    @property
    def name(self):
        return self.meta["login"]

    def can(self, action: str, value: Any = None, anyval=False) -> bool:
        if self["is_admin"]:
            return True
        key = f"can/{action}"

        if not self[key]:
            return False

        if anyval:
            return True

        if self[key] is True:
            return True

        if self[key] == value:
            return True

        if isinstance(self[key], list):
            if value in self[key]:
                return True

        return False


user = FireflyUser()
