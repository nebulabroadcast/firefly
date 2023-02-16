from functools import partial

import firefly
from firefly.config import config
from firefly.dialogs.about import show_about_dialog
from firefly.qt import QAction, QActionGroup

# FAKE DICT for the settings originally stored in config,
# but should be eventually moved to the settings
fake_config = {}


def create_menu(wnd):
    menubar = wnd.menuBar()

    menu_file = menubar.addMenu("&File")
    action_new_asset = QAction("&New asset", wnd)
    action_new_asset.setShortcut("Ctrl+N")
    action_new_asset.setStatusTip("Create new asset from template")
    action_new_asset.triggered.connect(wnd.new_asset)
    action_new_asset.setEnabled(
        firefly.user.can("asset_create") and fake_config.get("ui_asset_create", True)
    )
    menu_file.addAction(action_new_asset)

    action_clone_asset = QAction("&Clone asset", wnd)
    action_clone_asset.setShortcut("Ctrl+Shift+N")
    action_clone_asset.setStatusTip("Clone current asset")
    action_clone_asset.triggered.connect(wnd.clone_asset)
    action_clone_asset.setEnabled(
        firefly.user.can("asset_create") and fake_config.get("ui_asset_create", True)
    )
    menu_file.addAction(action_clone_asset)

    menu_file.addSeparator()

    action_refresh = QAction("&Refresh", wnd)
    action_refresh.setShortcut("F5")
    action_refresh.setStatusTip("Refresh views")
    action_refresh.triggered.connect(wnd.refresh)
    menu_file.addAction(action_refresh)

    action_load_settings = QAction("&Reload settings", wnd)
    action_load_settings.setShortcut("Shift+F5")
    action_load_settings.setStatusTip("Reload system settings")
    action_load_settings.triggered.connect(wnd.load_settings)
    menu_file.addAction(action_load_settings)

    menu_file.addSeparator()

    action_logout = QAction("L&ogout", wnd)
    action_logout.setStatusTip("Log out user")
    action_logout.triggered.connect(wnd.logout)
    menu_file.addAction(action_logout)

    action_exit = QAction("E&xit", wnd)
    action_exit.setShortcut("Alt+F4")
    action_exit.setStatusTip("Quit Firefly")
    action_exit.triggered.connect(wnd.exit)
    menu_file.addAction(action_exit)

    #
    # Browser
    #

    menu_browser = menubar.addMenu("Browser")

    action_detail = QAction("Asset &detail", wnd)
    action_detail.setShortcut("F2")
    action_detail.setStatusTip("Focus asset search bar")
    action_detail.triggered.connect(wnd.show_detail)
    menu_browser.addAction(action_detail)

    action_search = QAction("&Search assets", wnd)
    action_search.setShortcut("ESC")
    action_search.setStatusTip("Focus asset search bar")
    action_search.triggered.connect(wnd.search_assets)
    menu_browser.addAction(action_search)

    menu_browser.addSeparator()

    action_new_tab = QAction("&New tab", wnd)
    action_new_tab.setShortcut("CTRL+T")
    action_new_tab.setStatusTip("Open new browser tab")
    action_new_tab.triggered.connect(wnd.new_tab)
    menu_browser.addAction(action_new_tab)

    action_close_tab = QAction("&Close tab", wnd)
    action_close_tab.setShortcut("CTRL+W")
    action_close_tab.setStatusTip("Close current browser tab")
    action_close_tab.triggered.connect(wnd.close_tab)
    menu_browser.addAction(action_close_tab)

    action_prev_tab = QAction("&Previous tab", wnd)
    action_prev_tab.setShortcut("CTRL+PgUp")
    action_prev_tab.triggered.connect(wnd.prev_tab)
    menu_browser.addAction(action_prev_tab)

    action_next_tab = QAction("&Next tab", wnd)
    action_next_tab.setShortcut("CTRL+PgDown")
    action_next_tab.triggered.connect(wnd.next_tab)
    menu_browser.addAction(action_next_tab)

    #
    # Scheduling
    #

    if firefly.settings.playout_channels:
        wnd.menu_scheduler = menubar.addMenu("&Scheduler")
        ag = QActionGroup(wnd)
        ag.setExclusive(True)

        for playout_channel in firefly.settings.playout_channels:
            act = QAction(playout_channel.name, wnd)

            act.setCheckable(True)
            act.id_channel = playout_channel.id
            act.triggered.connect(partial(wnd.set_channel, playout_channel.id))
            if (
                firefly.user.can("rundown_view", playout_channel.id)
                or firefly.user.can("rundown_edit", playout_channel.id)
                or firefly.user.can("scheduler_view", playout_channel.id)
                or firefly.user.can("scheduler_edit", playout_channel.id)
            ):
                act.setEnabled(True)
            else:
                act.setEnabled(False)
            wnd.menu_scheduler.addAction(act)
            ag.addAction(act)

        wnd.menu_scheduler.addSeparator()

        action_import_template = QAction("Import", wnd)
        action_import_template.setStatusTip("Import week template")
        action_import_template.triggered.connect(wnd.import_template)
        wnd.menu_scheduler.addAction(action_import_template)

        action_export_template = QAction("Export", wnd)
        action_export_template.setStatusTip("Export current week as template")
        action_export_template.triggered.connect(wnd.export_template)
        wnd.menu_scheduler.addAction(action_export_template)

        #
        # Rundown
        #

        menu_rundown = menubar.addMenu("&Rundown")

        action_now = QAction("Now", wnd)
        action_now.setShortcut("F1")
        action_now.setStatusTip("Open current position in rundown")
        action_now.setEnabled(firefly.user.can("rundown_view"))
        action_now.triggered.connect(wnd.now)
        menu_rundown.addAction(action_now)

        wnd.action_rundown_edit = QAction("Rundown edit mode", wnd)
        wnd.action_rundown_edit.setShortcut("Ctrl+R")
        wnd.action_rundown_edit.setStatusTip("Toggle rundown edit mode")
        wnd.action_rundown_edit.setCheckable(True)
        wnd.action_rundown_edit.setEnabled(firefly.user.can("rundown_edit"))
        wnd.action_rundown_edit.triggered.connect(wnd.toggle_rundown_edit)
        menu_rundown.addAction(wnd.action_rundown_edit)

        menu_rundown.addSeparator()

        action_refresh_plugins = QAction("Refresh plugins", wnd)
        action_refresh_plugins.setStatusTip("Refresh rundown plugins")
        action_refresh_plugins.triggered.connect(wnd.refresh_plugins)
        menu_rundown.addAction(action_refresh_plugins)

    #
    # HELP
    #

    menu_help = menubar.addMenu("Help")

    wnd.action_debug = QAction("Debug mode", wnd)
    wnd.action_debug.setStatusTip("Toggle debug mode")
    wnd.action_debug.setCheckable(True)
    wnd.action_debug.setChecked(config.debug)
    wnd.action_debug.triggered.connect(wnd.toggle_debug_mode)

    menu_help.addAction(wnd.action_debug)
    menu_help.addSeparator()

    action_about = QAction("&About", wnd)
    action_about.setStatusTip("About Firefly")
    action_about.triggered.connect(partial(show_about_dialog, wnd))
    menu_help.addAction(action_about)
