__version__ = "6.0.1"

from firefly.config import config
from firefly.settings import Settings
from firefly.user import FireflyUser

assert config

settings = Settings()
user = FireflyUser()
