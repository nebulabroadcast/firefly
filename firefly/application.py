import os
import sys
import time
import locale

from typing import Any
from nxtools import logging, log_traceback, critical_error

import firefly

from firefly.filesystem import load_filesystem
from firefly.dialogs.login import show_login_dialog
from firefly.dialogs.site_select import show_site_select_dialog
from firefly.api import api
from firefly.config import config
from firefly.metadata import clear_cs_cache
from firefly.main_window import FireflyMainWindow, FireflyMainWidget
from firefly.objects import asset_cache
from firefly.version import FIREFLY_VERSION
from firefly.qt import (
    Qt,
    QApplication,
    QMessageBox,
    QSplashScreen,
    app_settings,
    app_dir,
    app_skin,
    pixlib,
)


def check_login(wnd):
    response = api.init()
    if not response:
        QMessageBox.critical(wnd, "Critical error", response.message)
        return False
    user_meta = response.get("user", False)
    if user_meta:
        return response
    if not show_login_dialog(wnd):
        return False
    response = api.init()
    if not response:
        QMessageBox.critical(wnd, "Login failed", response.message)
        return False
    return response


class FireflyApplication(QApplication):
    def __init__(self, **kwargs):
        super(FireflyApplication, self).__init__(sys.argv)
        self.app_state = {"name": "firefly", "title": f"Firefly {FIREFLY_VERSION}"}
        self.app_state_path = os.path.join(app_dir, f"{app_settings['name']}.appstate")
        self.setStyleSheet(app_skin)
        locale.setlocale(locale.LC_NUMERIC, "C")

        self.splash = QSplashScreen(pixlib["splash"])
        self.splash.setFixedSize(600, 600)
        self.splash.show()

        # Which site we are running

        i = 0
        if len(config.sites) > 1:
            i = show_site_select_dialog(self.splash)
        if i is None:
            sys.exit(0)
        config.set_site(i)

        self.app_state_path = os.path.join(
            app_dir, f"ffdata.{config.site.name}.appstate"
        )
        self.auth_key_path = os.path.join(app_dir, f"ffdata.{config.site.name}.key")

        # Login

        session_id = None
        try:
            session_id = open(self.auth_key_path).read()
        except FileNotFoundError:
            pass
        except Exception:
            log_traceback()
        config.site.token = session_id

        if not (init_response := check_login(self.splash)):
            logging.error("Unable to log in")
            sys.exit(0)

        firefly.user.update(init_response["user"])

        # Load settings and show main window
        self.splash_message("Loading site settings...")
        self.load_settings(init_response["settings"])
        self.splash_message("Loading filesystem...")
        load_filesystem()
        self.splash_message("Loading asset cache...")
        asset_cache.load()
        self.splash_message("Loading user workspace...")

        self.main_window = FireflyMainWindow(self, FireflyMainWidget)

    def start(self):
        self.splash.hide()
        try:
            self.exec()
        except Exception:
            log_traceback()
        logging.info("Shutting down")
        self.on_exit()

    def on_exit(self):
        asset_cache.save()
        if not self.main_window.listener:
            return
        if config.site.token:
            with open(self.auth_key_path, "w") as f:
                f.write(config.site.token)
        if not self.main_window.listener.halted:
            self.main_window.listener.halt()
            i = 0
            while not self.main_window.listener.halted:
                time.sleep(0.1)
                if i > 10:
                    logging.warning(
                        "Unable to shutdown listener. Forcing quit", handlers=False
                    )
                    break
                i += 1
        sys.exit(0)

    def splash_message(self, msg):
        if self.splash.isVisible:
            self.splash.showMessage(
                msg,
                alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                color=Qt.GlobalColor.white,
            )

    def load_settings(self, source: dict[str, Any] | None = None):
        self.splash_message("Loading site settings")

        if source is None:
            response = api.init()
            if not response:
                critical_error("Unable to load site settings")
            source = response["settings"]

        firefly.settings.update(source)
        clear_cs_cache()
