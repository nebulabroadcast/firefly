from nxtools import log_traceback
from firefly.application import FireflyApplication

if __name__ == "__main__":
    app = FireflyApplication()
    try:
        app.start()
    except Exception:
        log_traceback()
