from firefly.application import FireflyApplication
from firefly.log import log

if __name__ == "__main__":
    app = FireflyApplication()
    try:
        app.start()
    except Exception:
        log.traceback()
