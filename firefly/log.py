import enum
import sys
import traceback

from PySide6.QtWidgets import QMainWindow, QMessageBox

from firefly.config import config


def indent(text: str, level: int = 4) -> str:
    return text.replace("\n", f"\n{' '*level}")


class LogLevel(enum.IntEnum):
    """Log level."""

    TRACE = 0
    DEBUG = 1
    INFO = 2
    SUCCESS = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class Logger:
    level = LogLevel.TRACE
    main_window: QMainWindow | None = None

    def __call__(self, level: LogLevel, *args, **kwargs):
        if level < self.level:
            return
        if level < LogLevel.INFO and not config.debug:
            return
        print(
            f"{level.name.upper():<8}",
            " ".join([str(arg) for arg in args]),
            file=sys.stderr,
            flush=True,
        )

        if level >= LogLevel.ERROR:
            if self.main_window:
                msg = " ".join([str(arg) for arg in args])
                QMessageBox.critical(None, "Error", msg)

        self.status(*args)

    def status(self, *args, **kwargs):
        if self.main_window is None:
            return
        msg = " ".join([str(arg) for arg in args])
        self.main_window.statusBar().showMessage(msg)

    def trace(self, *args, **kwargs):
        self(LogLevel.TRACE, *args, **kwargs)

    def debug(self, *args, **kwargs):
        self(LogLevel.DEBUG, *args, **kwargs)

    def info(self, *args, **kwargs):
        self(LogLevel.INFO, *args, **kwargs)

    def success(self, *args, **kwargs):
        self(LogLevel.SUCCESS, *args, **kwargs)

    def warn(self, *args, **kwargs):
        self(LogLevel.WARNING, *args, **kwargs)

    def warning(self, *args, **kwargs):
        self(LogLevel.WARNING, *args, **kwargs)

    def error(self, *args, **kwargs):
        self(LogLevel.ERROR, *args, **kwargs)

    def traceback(self, *args, **kwargs):
        msg = " ".join([str(arg) for arg in args])
        tb = traceback.format_exc()
        msg = f"{msg}\n\n{indent(tb)}"
        self(LogLevel.ERROR, msg, **kwargs)

    def critical(self, *args, **kwargs):
        self(LogLevel.CRITICAL, *args, **kwargs)


log = Logger()
