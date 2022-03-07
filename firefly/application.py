import os
import sys
import time
import locale

from nxtools import logging, log_traceback, critical_error

from firefly.filesystem import load_filesystem

from firefly.dialogs.login import show_login_dialog
from firefly.dialogs.site_select import show_site_select_dialog

from firefly.api import api
from firefly.common import pixlib
from firefly.core.common import config
from firefly.core.metadata import clear_cs_cache
from firefly.objects import user
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
)


def check_login(wnd):
    data = api.ping()
    user_meta = data.get("data", False)
    if user_meta:
        session_id = data.get("session_id", False)
        if session_id:
            config["session_id"] = session_id
        return user_meta
    if data["response"] > 403:
        QMessageBox.critical(wnd, f"Error {data['response']}", data["message"])
        return False
    return show_login_dialog()


class FireflyApplication(QApplication):
    def __init__(self, **kwargs):
        super(FireflyApplication, self).__init__(sys.argv)
        self.app_state = {"name": "firefly", "title": f"Firefly {FIREFLY_VERSION}"}
        self.app_state_path = os.path.join(app_dir, f"{app_settings['name']}.appstate")
        self.setStyleSheet(app_skin)
        locale.setlocale(locale.LC_NUMERIC, "C")
        self.splash = QSplashScreen(pixlib["splash"])
        self.splash.show()

        # Which site we are running

        i = 0
        if "sites" in config:
            if len(config["sites"]) > 1:
                i = show_site_select_dialog()
            else:
                i = 0

        self.local_keys = list(config["sites"][i].keys())
        config.update(config["sites"][i])
        del config["sites"]

        self.app_state_path = os.path.join(
            app_dir, f"ffdata.{config['site_name']}.appstate"
        )
        self.auth_key_path = os.path.join(app_dir, f"ffdata.{config['site_name']}.key")

        # Login

        session_id = None
        try:
            session_id = open(self.auth_key_path).read()
        except FileNotFoundError:
            pass
        except Exception:
            log_traceback()
        config["session_id"] = session_id

        user_meta = check_login(self.splash)
        if not user_meta:
            logging.error("Unable to log in")
            sys.exit(0)
        user.meta = user_meta

        # Load settings and show main window
        self.splash_message("Loading site settings...")
        self.load_settings()
        self.splash_message("Loading filesystem...")
        load_filesystem()
        self.splash_message("Loading asset cache...")
        asset_cache.load()
        self.splash_message("Loading user workspace...")
        self.main_window = FireflyMainWindow(self, FireflyMainWidget)

    def start(self):
        self.splash.hide()
        try:
            self.exec_()
        except Exception:
            log_traceback()
        logging.info("Shutting down")
        self.on_exit()

    def on_exit(self):
        asset_cache.save()
        if not self.main_window.listener:
            return
        if config.get("session_id"):
            with open(self.auth_key_path, "w") as f:
                f.write(config["session_id"])
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
                msg, alignment=Qt.AlignBottom | Qt.AlignLeft, color=Qt.white
            )

    def load_settings(self):
        self.splash_message("Loading site settings")
        response = api.settings()
        if not response:
            QMessageBox.critical(self.splash, "Error", response.message)
            critical_error("Unable to load site settings")

        for key in response.data:
            if config.get(key) and key != "site_name":
                if key in self.local_keys:
                    continue
            config[key] = response.data[key]

        # Fix indices
        for config_group in [
            "storages",
            "playout_channels",
            "ingest_channels",
            "folders",
            "views",
            "actions",
            "services",
        ]:
            ng = {}
            for id in config[config_group]:
                ng[int(id)] = config[config_group][id]
            config[config_group] = ng
        clear_cs_cache()
