from functools import partial

from .common import *

def create_menu(wnd):
    menubar = wnd.menuBar()

    menu_file = menubar.addMenu('&File')
    action_new_asset = QAction('&New asset', wnd)
    action_new_asset.setShortcut('Ctrl+N')
    action_new_asset.setStatusTip('Create new asset from template')
    action_new_asset.triggered.connect(wnd.new_asset)
    action_new_asset.setEnabled(has_right("asset_create"))
    menu_file.addAction(action_new_asset)

    action_clone_asset = QAction('&Clone asset', wnd)
    action_clone_asset.setShortcut('Ctrl+Shift+N')
    action_clone_asset.setStatusTip('Create new asset from current blabla')
    action_clone_asset.triggered.connect(wnd.clone_asset)
    action_clone_asset.setEnabled(has_right("asset_create"))
    menu_file.addAction(action_clone_asset)

    menu_file.addSeparator()

    action_search = QAction('&Search assets', wnd)
    action_search.setShortcut('ESC')
    action_search.setStatusTip('Focus asset search bar')
    action_search.triggered.connect(wnd.search_assets)
    menu_file.addAction(action_search)

    action_detail = QAction('Asset &detail', wnd)
    action_detail.setShortcut('F2')
    action_detail.setStatusTip('Focus asset search bar')
    action_detail.triggered.connect(wnd.show_detail)
    menu_file.addAction(action_detail)

    action_refresh = QAction('&Refresh', wnd)
    action_refresh.setShortcut('F5')
    action_refresh.setStatusTip('Refresh views')
    action_refresh.triggered.connect(wnd.refresh)
    menu_file.addAction(action_refresh)

    menu_file.addSeparator()

    action_logout = QAction('L&ogout', wnd)
    action_logout.setStatusTip('Log out user')
    action_logout.triggered.connect(wnd.logout)
    menu_file.addAction(action_logout)

    action_exit = QAction('E&xit', wnd)
    action_exit.setShortcut('Alt+F4')
    action_exit.setStatusTip('Quit Firefly')
    action_exit.triggered.connect(wnd.exit)
    menu_file.addAction(action_exit)

#
# Scheduling
#

    if config["playout_channels"]:
        wnd.menu_scheduler = menubar.addMenu('&Scheduler')
        ag = QActionGroup(wnd, exclusive=True)

        for id_channel in sorted(config["playout_channels"]):
            a = ag.addAction(
                    QAction(
                        config["playout_channels"][id_channel]["title"],
                        wnd,
                        checkable=True
                    ))
            a.id_channel = id_channel
            a.triggered.connect(partial(wnd.set_channel, id_channel))
            wnd.menu_scheduler.addAction(a)

        wnd.menu_scheduler.addSeparator()

        action_import_template = QAction('Import', wnd)
        action_import_template.setStatusTip('Import week template')
        action_import_template.triggered.connect(wnd.import_template)
        wnd.menu_scheduler.addAction(action_import_template)

        action_export_template = QAction('Export', wnd)
        action_export_template.setStatusTip('Export current week as template')
        action_export_template.triggered.connect(wnd.export_template)
        wnd.menu_scheduler.addAction(action_export_template)

#
# Rundown
#

        menu_rundown = menubar.addMenu('&Rundown')

        action_now = QAction('Now', wnd)
        action_now.setShortcut('F1')
        action_now.setStatusTip('Open current position in rundown')
        action_now.setEnabled(has_right("rundown_view"))
        action_now.triggered.connect(wnd.now)
        menu_rundown.addAction(action_now)

        menu_rundown.addSeparator()

        action_refresh_plugins = QAction('Refresh plugins', wnd)
        action_refresh_plugins.setStatusTip('Refresh rundown plugins')
        action_refresh_plugins.triggered.connect(wnd.refresh_plugins)
        menu_rundown.addAction(action_refresh_plugins)


#
# HELP
#

    menu_help = menubar.addMenu('Help')
    action_about = QAction('&About', wnd)
    action_about.setStatusTip('About Firefly')
    action_about.triggered.connect(partial(about_dialog, wnd))
    menu_help.addAction(action_about)
