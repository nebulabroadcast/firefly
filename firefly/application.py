import sys
import locale
import copy

from pprint import pprint

from .common import *
from .filesystem import load_filesystem

from .dialogs.login import *
from .dialogs.site_select import *

from .main_window import FireflyMainWindow, FireflyMainWidget
from nebulacore.meta_utils import clear_cs_cache


def check_login(wnd):
    data = api.ping()
    user_meta = data.get("data", False)
    if user_meta:
        session_id = data.get("session_id", False)
        if session_id:
            config["session_id"] = session_id
        return user_meta
    if data["response"] > 403:
        QMessageBox.critical(
                wnd,
                "Error {}".format(data["response"]),
                data["message"]
            )
        return False
    return login_dialog()


class FireflyApplication(Application):
    def __init__(self, **kwargs):
        title = "Firefly {}".format(FIREFLY_VERSION)
        if FIREFLY_STATUS:
            title += " " + FIREFLY_STATUS
        super(FireflyApplication, self).__init__(name="firefly", title=title)
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.splash = QSplashScreen(pix_lib['splash'])
        self.splash.show()

        # Which site we are running

        i = 0
        if "sites" in config:
            if len(config["sites"]) > 1:
                i = site_select_dialog()
            else:
                i = 0

        self.local_keys = list(config["sites"][i].keys())
        config.update(config["sites"][i])
        del(config["sites"])

        self.app_state_path = os.path.join(app_dir, "ffdata.{}.appstate".format(config["site_name"]))
        self.auth_key_path = os.path.join(app_dir,  "ffdata.{}.key".format(config["site_name"]))

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
                time.sleep(.1)
                if i > 10:
                    logging.warning("Unable to shutdown listener. Forcing quit", handlers=False)
                    break
                i+=1
        sys.exit(0)

    def splash_message(self, msg):
        if self.splash.isVisible:
            self.splash.showMessage(
                    msg,
                    alignment=Qt.AlignBottom|Qt.AlignLeft,
                    color=Qt.white
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
