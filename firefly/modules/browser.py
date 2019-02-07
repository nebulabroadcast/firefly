import math
import functools

from firefly import *
from firefly.dialogs.send_to import *

from .browser_model import *


class SearchWidget(QLineEdit):
    def __init__(self, parent):
        super(QLineEdit, self).__init__()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return,Qt.Key_Enter]:
            self.parent().load()
        elif event.key() == Qt.Key_Escape:
            self.line_edit.setText("")
        elif event.key() == Qt.Key_Down:
            self.parent().view.setFocus()
        QLineEdit.keyPressEvent(self, event)


class FireflyBrowserView(FireflyView):
    def __init__(self, parent):
        super(FireflyBrowserView, self).__init__(parent)
        self.setSortingEnabled(True)
        self.model = BrowserModel(self)
        self.sort_model = FireflySortModel(self.model)
        self.setModel(self.sort_model)

    def selectionChanged(self, selected, deselected):
        rows = []
        self.selected_objects = []

        tot_dur = 0
        for idx in self.selectionModel().selectedIndexes():
            row = self.sort_model.mapToSource(idx).row()
            if row in rows:
                continue
            rows.append(row)
            obj = self.model.object_data[row]
            self.selected_objects.append(obj)
            if obj.object_type in ["asset", "item"]:
                tot_dur += obj.duration

        days = math.floor(tot_dur / (24*3600))
        durstr = "{} days {}".format(days, s2time(tot_dur)) if days else s2time(tot_dur)

        if self.selected_objects:
            self.main_window.focus(asset_cache[self.selected_objects[-1].id])
            if len(self.selected_objects) > 1 and tot_dur:
                logging.debug(
                        "[BROWSER] {} objects selected. Total duration {}".format(
                            len(self.selected_objects), durstr
                        )
                    )
        super(FireflyView, self).selectionChanged(selected, deselected)







class BrowserTab(QWidget):
    def __init__(self, parent, **kwargs):
        super(BrowserTab, self).__init__(parent)
        self._parent = parent
        self.loading = False

        # Search query

        self.search_query = {
                "id_view" : kwargs.get("id_view", min(config["views"])),
                "fulltext" : kwargs.get("fulltext", "")
            }

        # Layout

        self.search_box = SearchWidget(self)
        if self.search_query.get("fulltext"):
            self.search_box.setText(self.search_query["fulltext"])

        self.first_load = True
        self.view = FireflyBrowserView(self)
        self.view.horizontalHeader().sectionResized.connect(self.on_section_resize)

        action_clear = QAction(QIcon(pix_lib["cancel"]), '&Clear search query', parent)
        action_clear.triggered.connect(self.on_clear)

        self.action_search = QMenu("Views")
        self.action_search.setStyleSheet(app_skin)
        self.action_search.menuAction().setIcon(QIcon(pix_lib["search"]))
        self.action_search.menuAction().triggered.connect(self.load)
        self.load_view_menu()

        action_copy = QAction('Copy result', self)
        action_copy.setShortcut('CTRL+SHIFT+C')
        action_copy.triggered.connect(self.on_copy_result)
        self.addAction(action_copy)


        toolbar = QToolBar(self)
        toolbar.addAction(action_clear)
        toolbar.addAction(self.action_search.menuAction())

        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0,0,0,0)
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(toolbar)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addLayout(search_layout, 0)
        layout.addWidget(self.view, 1)
        self.setLayout(layout)

    @property
    def model(self):
        return self.view.model

    @property
    def id_view(self):
        return self.search_query["id_view"]

    @property
    def main_window(self):
        return self._parent.main_window

    @property
    def app_state(self):
        return self._parent.app_state

    def load_view_menu(self):
        i = 1
        for id_view in sorted(
                    config["views"].keys(),
                    key=lambda k: config["views"][k]["position"]
                ):
            view = config["views"][id_view]
            if view["title"] == "-":
                self.action_search.addSeparator()
                continue
            action = QAction(view["title"], self, checkable=True)
            action.setShortcut("ALT+{}".format(i))
            action.id_view = id_view
            action.triggered.connect(functools.partial(self.set_view, id_view))
            self.action_search.addAction(action)
            i+=1

    def on_section_resize(self, *args, **kwargs):
        if self.loading:
            return
        if not "browser_view_sizes" in self.app_state:
            self.app_state["browser_view_sizes"] = {}
        if not "browser_default_sizes"in self.app_state:
            self.app_state["browser_default_sizes"] = {}

        data = {}
        for i, h in enumerate(self.model.header_data):
            w = self.view.horizontalHeader().sectionSize(i)
            self.app_state["browser_default_sizes"][h] = w
            data[h] = w
        self.app_state["browser_view_sizes"][self.id_view] = data

#
# Do browse
#

    def load(self, **kwargs):
        self.loading = True
        old_view = self.search_query.get("id_view", -1)
        search_string = self.search_box.text()
        self.search_query["fulltext"] = search_string
        self.search_query.update(kwargs)
        self.view.model.load(**self.search_query)

        if self.first_load or self.id_view != old_view:
            view_state = self.app_state.get("browser_view_sizes", {}).get(self.id_view, {})
            default_sizes = self.app_state.get("browser_defaut_sizes", {})
            for i, h in enumerate(self.model.header_data):
                if h in view_state:
                    w = view_state[h]
                elif h in default_sizes:
                    w = default_sizes[h]
                elif h in ["title", "subtitle"]:
                    w = 300
                elif h in ["qc/state"]:
                    w = 20
                else:
                    w = 120
                self.view.horizontalHeader().resizeSection(i, w)
            self.first_load = False
        self.loading = False
        self._parent.redraw_tabs()

    def on_clear(self):
        self.search_box.setText("")
        self.load(fulltext="")

    def set_view(self, id_view):
        self.load(id_view=id_view)
        for action in self.action_search.actions():
            if not hasattr(action, "id_view"):
                continue
            if action.id_view == id_view:
                action.setChecked(True)
            else:
                action.setChecked(False)
        self.app_state["id_view"] = id_view


    def contextMenuEvent(self, event):
        if not self.view.selected_objects:
            return
        menu = QMenu(self)

        statuses = []
        for obj in self.view.selected_objects:
            status = obj["status"]
            if not status in statuses:
                statuses.append(status)
        allstat = -1
        if len(statuses) == 1:
            allstat = statuses[0]

        if allstat == TRASHED:
            action_untrash = QAction('Untrash', self)
            action_untrash.setStatusTip('Take selected asset(s) from trash')
            action_untrash.triggered.connect(self.on_untrash)
            menu.addAction(action_untrash)

        elif allstat == ARCHIVED:
            action_unarchive = QAction('Unarchive', self)
            action_unarchive.setStatusTip('Take selected asset(s) from archive')
            action_unarchive.triggered.connect(self.on_unarchive)
            menu.addAction(action_unarchive)

        elif allstat in [ONLINE, CREATING, OFFLINE]:
            action_move_to_trash = QAction('Move to trash', self)
            action_move_to_trash.setStatusTip('Move selected asset(s) to trash')
            action_move_to_trash.triggered.connect(self.on_trash)
            menu.addAction(action_move_to_trash)

            action_move_to_archive = QAction('Move to archive', self)
            action_move_to_archive.setStatusTip('Move selected asset(s) to archive')
            action_move_to_archive.triggered.connect(self.on_archive)
            menu.addAction(action_move_to_archive)


        action_reset = QAction('Reset', self)
        action_reset.setStatusTip('Reload asset metadata')
        action_reset.triggered.connect(self.on_reset)
        menu.addAction(action_reset)

        menu.addSeparator()

        action_send_to = QAction('&Send to...', self)
        action_send_to.setStatusTip('Create action for selected asset(s)')
        action_send_to.triggered.connect(self.on_send_to)
        menu.addAction(action_send_to)

#TODO
#        menu.addSeparator()
#        action_columns = QAction('Choose columns', self)
#        action_columns.setStatusTip('Choose header columns')
#        action_columns.triggered.connect(self.on_choose_columns)
#        menu.addAction(action_columns)

        menu.exec_(event.globalPos())


    def on_send_to(self):
        send_to_dialog(self.view.selected_objects)

    def on_reset(self):
        objects = [obj.id for obj in self.view.selected_objects if obj["status"] not in [ARCHIVED, TRASHED, RESET]],
        if not objects:
            return
        response = api.set(
                objects=objects,
                data={"status" : RESET}
            )

    def on_trash(self):
        objects = [obj.id for obj in self.view.selected_objects if obj["status"] not in [ARCHIVED, TRASHED]]
        if not objects:
            return
        ret = QMessageBox.question(self,
                "Trash",
                "Do you really want to trash {} selected asset(s)?".format(len(objects)),
                QMessageBox.Yes | QMessageBox.No
            )
        if ret == QMessageBox.Yes:
            response = api.set(
                    objects=objects,
                    data={"status" : TRASHED}
                )
        else:
            return
        if not response:
            logging.error("Unable to trash:\n\n" + response.message)

    def on_untrash(self):
        objects = [obj.id for obj in self.view.selected_objects if obj["status"] in [TRASHED]]
        if not objects:
            return
        response = api.set(
                objects=objects,
                data={"status" : CREATING}
            )
        if not response:
            logging.error("Unable to untrash:\n\n" + response.message)

    def on_archive(self):
        objects = [obj.id for obj in self.view.selected_objects if obj["status"] not in [ARCHIVED, TRASHED]]
        if not objects:
            return
        ret = QMessageBox.question(self,
                "Archive",
                "Do you really want to move {} selected asset(s) to archive?".format(len(objects)),
                QMessageBox.Yes | QMessageBox.No
            )
        if ret == QMessageBox.Yes:
            response = api.set(
                    objects=objects,
                    data={"status" : ARCHIVED}
                )
        else:
            return
        if not response:
            logging.error("Unable to archive:\n\n" + response.message)

    def on_unarchive(self):
        objects = [obj.id for obj in self.view.selected_objects if obj["status"] in [ARCHIVED]]
        if not objects:
            return
        response = api.set(
                objects=objects,
                data={"status" : RETRIEVING}
            )
        if not response:
            logging.error("Unable to unarchive:\n\n" + response.message)


    def on_choose_columns(self):
        #TODO
        logging.error("Not implemented")


    def on_copy_result(self):
        result = ""
        for obj in self.view.selected_objects:
            result += "{}\n".format("\t".join([obj.format_display(key) or "" for key in self.view.model.header_data]))
        clipboard = QApplication.clipboard();
        clipboard.setText(result)

    def seismic_handler(self, message):
            for row, obj in enumerate(self.model.object_data):
                if obj.id in message.data["objects"]:
                    self.model.object_data[row] = asset_cache[obj.id]
                    self.model.dataChanged.emit(self.model.index(row, 0), self.model.index(row, len(self.model.header_data)-1))


class BrowserModule(BaseModule):
    def __init__(self, parent):
        super(BrowserModule, self).__init__(parent)
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

        tabscfg = self.app_state.get("browser_tabs", [])
        created_tabs = 0
        for tabcfg in tabscfg:
            try:
                if tabcfg["id_view"] not in config["views"]:
                    continue
                self.new_tab(**tabcfg)
                created_tabs += 1
            except Exception:
                log_traceback()
                logging.warning("Unable to restore tab")
        if not created_tabs:
            self.new_tab()

    def new_tab(self, **kwargs):
        if not "id_view" in kwargs:
            try:
                id_view = self.tabs.currentWidget().id_view
            except AttributeError:
                pass
            else:
                kwargs["id_view"] = id_view
        tab = BrowserTab(self, **kwargs)
        self.tabs.addTab(tab, "New tab")
        self.tabs.setCurrentIndex(self.tabs.indexOf(tab))
        tab.load()


    def close_tab(self, idx=False):
        if self.tabs.count() == 1:
            return
        if not idx:
            idx = self.tabs.currentIndex()
        w = self.tabs.widget(idx)
        w.deleteLater()
        self.tabs.removeTab(idx)
        self.redraw_tabs()

    def prev_tab(self):
        cur = self.tabs.currentIndex()
        if cur == 0:
            n = self.tabs.count() -  1
        else:
            n = cur -1
        self.tabs.setCurrentIndex(n)

    def next_tab(self):
        cur = self.tabs.currentIndex()
        if cur == self.tabs.count() - 1:
            n = 0
        else:
            n = cur + 1
        self.tabs.setCurrentIndex(n)

    def load(self):
        for b in self.browsers:
            b.load()

    def seismic_handler(self, message):
        if message.method == "objects_changed" and message.data["object_type"] == "asset":
            for b in self.browsers:
                b.seismic_handler(message)

    @property
    def browsers(self):
        r = []
        for i in range(0,self.tabs.count()):
            r.append(self.tabs.widget(i))
        return r

    def redraw_tabs(self):
        QApplication.processEvents()
        views = []
        for i,b in enumerate(self.browsers):
            id_view = b.id_view
            self.tabs.setTabText(i, config["views"][id_view]["title"])
            views.append(b.search_query)
        self.app_state["browser_tabs"] = views
