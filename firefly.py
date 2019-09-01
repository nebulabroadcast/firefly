#!/usr/bin/env python3

try:
    import rex
except ImportError:
    # Freezed application does not need package manager
    pass

from nxtools import *
from firefly.application import FireflyApplication

if __name__ == "__main__":
    app = FireflyApplication()
    try:
        app.start()
    except Exception:
        log_traceback()
