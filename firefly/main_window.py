import queue
import time


import firefly

from firefly.api import api
from firefly.config import config
from firefly.log import log
from firefly.listener import SeismicListener
from firefly.menu import create_menu
from firefly.modules import (
    BrowserModule,
    DetailModule,
    JobsModule,
    RundownModule,
    SchedulerModule,
)
from firefly.objects import asset_cache
from firefly.qt import (
    QApplication,
    QIcon,
    QMainWindow,
    QMessageBox,
    QSplitter,
    Qt,
    QTabWidget,
    QTimer,
    QVBoxLayout,
    QWidget,
    app_settings,
    app_skin,
    get_app_state,
    pixlib,
)


class FireflyMainWidget(QWidget):
    def __init__(self, main_window):
        super(FireflyMainWidget, self).__init__(main_window)
        self.main_window = main_window
        current_tab = self.main_window.app_state.get("current_module", 0)
        self.perform_on_switch_tab = True

        self.tabs = QTabWidget(self)

        self.browser = self.detail = self.rundown = self.scheduler = self.jobs = None

        # MAM modules

        self.browser = BrowserModule(self)
        self.detail = DetailModule(self)
        self.tabs.addTab(self.detail, "DETAIL")

        self.main_window.add_subscriber(self.browser, ["objects_changed"])
        self.main_window.add_subscriber(self.detail, ["objects_changed"])

        # Jobs module

        self.jobs = JobsModule(self)
        self.tabs.addTab(self.jobs, "JOBS")
        self.main_window.add_subscriber(self.jobs, ["job_progress"])

        # Channel control modules

        if firefly.settings.playout_channels:
            if firefly.user.can("scheduler_view", anyval=True) or firefly.user.can(
                "scheduler_edit", anyval=True
            ):
                self.scheduler = SchedulerModule(self)
                self.main_window.add_subscriber(self.scheduler, ["objects_changed"])
                self.tabs.addTab(self.scheduler, "SCHEDULER")

            if firefly.user.can("rundown_view", anyval=True) or firefly.user.can(
                "rundown_edit", anyval=True
            ):
                self.rundown = RundownModule(self)
                self.main_window.add_subscriber(
                    self.rundown,
                    [
                        "objects_changed",
                        "rundown_changed",
                        "playout_status",
                        "job_progress",
                    ],
                )
                self.tabs.addTab(self.rundown, "RUNDOWN")

        # Layout

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(12)
        self.main_splitter.addWidget(self.browser)
        self.main_splitter.addWidget(self.tabs)
        self.main_splitter.splitterMoved.connect(self.main_window.save_window_state)

        create_menu(self.main_window)

        layout = QVBoxLayout()
        layout.addWidget(self.main_splitter)
        self.setLayout(layout)

        if current_tab:
            self.switch_tab(current_tab)
        else:
            self.on_switch_tab()

        self.tabs.currentChanged.connect(self.on_switch_tab)

    def on_close(self):
        if self.detail:
            self.detail.check_changed()
        self.main_window.listener.halt()
        QApplication.quit()
        log.debug("[MAIN WINDOW] Window closed")

    @property
    def app(self):
        return self.main_window.app

    @property
    def current_module(self):
        return self.tabs.currentWidget()

    def switch_tab(self, module, perform_on_switch_tab=True):
        self.perform_on_switch_tab = perform_on_switch_tab
        for i in range(self.tabs.count()):
            if (type(module) == int and module == i) or self.tabs.widget(i) == module:
                self.tabs.setCurrentIndex(i)

    def on_switch_tab(self, index=None):
        if self.perform_on_switch_tab:
            if self.detail:
                if self.current_module == self.detail:
                    self.detail.detail_tabs.on_switch()
                else:
                    # Disable proxy loading if player is not focused
                    self.detail.detail_tabs.on_switch(-1)

            if self.rundown and (self.current_module == self.rundown):
                if self.rundown.mcr and self.rundown.mcr.isVisible():
                    self.rundown.mcr.request_display_resize = True
                # Refresh rundown on focus
                self.rundown.load()

            if self.jobs and (self.current_module == self.jobs):
                self.jobs.load()

        self.main_window.app_state["current_module"] = self.tabs.currentIndex()
        self.perform_on_switch_tab = True


class FireflyMainWindow(QMainWindow):
    def __init__(self, parent, MainWidgetClass):
        super(FireflyMainWindow, self).__init__()

        self.subscribers = []
        asset_cache.api = api
        asset_cache.handler = self.on_assets_update

        self.setWindowTitle(app_settings["title"])
        self.setStyleSheet(app_skin)
        self.app = parent
        self.restore_state()
        self.main_widget = MainWidgetClass(self)
        self.setCentralWidget(self.main_widget)
        self.show()

        self.setWindowIcon(QIcon(pixlib["icon"]))
        title = f"Firefly {firefly.__version__}"
        title += f" ({firefly.user}@{config.site.name})"
        self.setWindowTitle(title)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        log.main_window = self
        self.listener = SeismicListener()

        self.seismic_timer = QTimer(self)
        self.seismic_timer.timeout.connect(self.on_seismic_timer)
        self.seismic_timer.start(40)

        self.load_window_state()

        for playout_channel in firefly.settings.playout_channels:
            if (
                firefly.user.can("rundown_view", playout_channel.id)
                or firefly.user.can("rundown_edit", playout_channel.id)
                or firefly.user.can("scheduler_view", playout_channel.id)
                or firefly.user.can("scheduler_edit", playout_channel.id)
            ):
                self.id_channel = firefly.settings.playout_channels[0].id
                self.set_channel(self.id_channel)
                break

        log.info("[MAIN WINDOW] Firefly is ready")

    #
    #
    #

    @property
    def app_state(self):
        return self.app.app_state

    @app_state.setter
    def app_state(self, value):
        self.app.app_state = value

    def save_state(self):
        state = get_app_state(self.app.app_state_path)
        state.setValue("main_window/state", self.saveState())
        state.setValue("main_window/geometry", self.saveGeometry())
        state.setValue("main_window/app", self.app_state)

    def restore_state(self):
        state = get_app_state(self.app.app_state_path)
        if "main_window/geometry" in state.allKeys():
            self.restoreGeometry(state.value("main_window/geometry"))
            self.restoreState(state.value("main_window/state"))
        else:
            self.resize(800, 600)
            qr = self.frameGeometry()
            # cp = QDesktopWidget().availableGeometry().center()
            # qr.moveCenter(cp)
            self.move(qr.topLeft())
        if "main_window/app" in state.allKeys():
            try:
                self.app_state = state.value("main_window/app")
            except Exception:
                log.traceback()


    def closeEvent(self, event):
        self.save_state()
        if hasattr(self.main_widget, "on_close"):
            self.main_widget.on_close()

    #
    #
    #

    def load_window_state(self):
        self.window_state = self.app_state.get("window_state", {})
        self.showMaximized()
        one_third = self.width() / 3
        sizes = self.window_state.get("splitter_sizes", [one_third, one_third * 2])
        self.main_widget.main_splitter.setSizes(sizes)

    def save_window_state(self, *args, **kwargs):
        state = {"splitter_sizes": self.main_widget.main_splitter.sizes()}
        self.app_state["window_state"] = state

    @property
    def current_module(self):
        return self.main_widget.current_module

    @property
    def browser(self):
        return self.main_widget.browser

    @property
    def scheduler(self):
        return self.main_widget.scheduler

    @property
    def rundown(self):
        return self.main_widget.rundown

    @property
    def detail(self):
        return self.main_widget.detail

    @property
    def jobs(self):
        return self.main_widget.jobs

    def focus(self, obj):
        if type(obj) == list:
            obj = obj[0]
        if obj.object_type == "item":
            obj = obj.asset
        self.detail.focus(obj)
        if self.scheduler:
            self.scheduler.focus(obj)

    #
    # Menu actions
    #

    def new_asset(self):
        self.detail.new_asset()

    def clone_asset(self):
        self.detail.clone_asset()

    def logout(self):
        response = api.logout(api="1")
        log.info(response["message"])
        self.close()

    def exit(self):
        self.close()

    def new_tab(self):
        self.browser.new_tab()

    def close_tab(self):
        self.browser.close_tab()

    def prev_tab(self):
        self.browser.prev_tab()

    def next_tab(self):
        self.browser.next_tab()

    def search_assets(self):
        search_box = self.browser.tabs.currentWidget().search_box
        search_box.setFocus()
        search_box.selectAll()

    def now(self):
        if firefly.settings.playout_channels and (
            firefly.user.can("rundown_view", self.id_channel)
            or firefly.user.can("rundown_edit", self.id_channel)
        ):
            self.show_rundown()
            self.rundown.go_now()

    def toggle_rundown_edit(self):
        if firefly.settings.playout_channels and firefly.user.can(
            "rundown_edit", self.id_channel
        ):
            self.rundown.toggle_rundown_edit()

    def toggle_debug_mode(self):
        config.debug = not config.debug

    def refresh_plugins(self):
        self.rundown.plugins.load()

    def set_channel(self, id_channel):
        if firefly.settings.playout_channels:
            for action in self.menu_scheduler.actions():
                if hasattr(action, "id_channel") and action.id_channel == id_channel:
                    action.setChecked(True)
            self.id_channel = id_channel
            if self.scheduler:
                self.scheduler.on_channel_changed()
            if self.rundown:
                self.rundown.on_channel_changed()

    def show_detail(self):
        if self.main_widget.tabs.currentIndex() == 0:
            self.detail.switch_tabs()
        else:
            self.main_widget.tabs.setCurrentIndex(0)

    def show_scheduler(self):
        if firefly.settings.playout_channels and (
            firefly.user.can("scheduler_view", self.id_channel)
            or firefly.user.can("scheduler_edit", self.id_channel)
        ):
            self.main_widget.switch_tab(self.scheduler)

    def show_rundown(self):
        if firefly.settings.playout_channels and (
            firefly.user.can("rundown_view", self.id_channel)
            or firefly.user.can("rundown_edit", self.id_channel)
        ):
            self.main_widget.switch_tab(self.rundown)

    def refresh(self):
        self.browser.load()
        if firefly.settings.playout_channels:
            if self.rundown:
                self.rundown.load()
            if self.scheduler:
                self.scheduler.load()
            if self.detail:
                if self.detail.asset:
                    self.detail.focus(self.detail.asset, force=True)

    def load_settings(self):
        log.info("[MAIN WINDOW] Reloading system settings")
        self.app.load_settings()
        self.refresh()

    def export_template(self):
        self.scheduler.export_template()

    def import_template(self):
        self.scheduler.import_template()

    #
    # Messaging
    #

    def on_seismic_timer(self):
        now = time.time()
        if now - self.listener.last_msg > 5:
            log.debug(
                "[MAIN WINDOW] No seismic message received. Something may be wrong"
            )
            self.listener.last_msg = time.time()
        while True:
            try:
                message = self.listener.queue.get_nowait()
            except queue.Empty:
                return
            else:
                self.seismic_handler(message)

    def add_subscriber(self, module, methods):
        self.subscribers.append([module, frozenset(methods)])

    def seismic_handler(self, message):
        if (
            message.method == "objects_changed"
            and message.data["object_type"] == "asset"
        ):
            objects = message.data["objects"]
            log.debug(f"[MAIN WINDOW] {len(objects)} asset(s) have been changed")
            asset_cache.request([[aid, message.timestamp + 1] for aid in objects])
            return

        if message.method == "config_changed":
            self.load_settings()
            return

        for module, methods in self.subscribers:
            if message.method in methods:
                module.seismic_handler(message)

    def on_assets_update(self, *assets):
        log.debug(f"[MAIN WINDOW] Updating {len(assets)} assets in views")

        self.browser.refresh_assets(*assets)
        self.detail.refresh_assets(*assets)
        if self.rundown:
            self.rundown.refresh_assets(*assets)
