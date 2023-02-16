__version__ = "6.0.0-beta.1"

from nxtools import logging

from firefly.config import config
from firefly.settings import Settings
from firefly.user import FireflyUser

logging.user = ""
logging.handlers = []

assert config

settings = Settings()
user = FireflyUser()
