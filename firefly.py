#!/usr/bin/env python3

try:
    import rex
except ImportError:
    # Freezed application does not need package manager
    pass

from firefly.application import FireflyApplication

if __name__ == "__main__":
    app = FireflyApplication()
    app.start()
