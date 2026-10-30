__version__ = "6.0.3"

from firefly.config import config
from firefly.settings import Settings
from firefly.user import FireflyUser

__all__ = ["config", "settings", "user"]

settings = Settings()
user = FireflyUser()
