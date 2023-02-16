__version__ = "6.0.0-beta.1"

from firefly.config import config
from firefly.settings import Settings
from firefly.user import FireflyUser

from nxtools import logging

logging.user = ""
logging.handlers = []

assert config

settings = Settings()
user = FireflyUser()
