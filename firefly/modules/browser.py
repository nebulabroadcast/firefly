import copy
import functools

from nxtools import logging, log_traceback

from firefly.api import api
from firefly.common import pixlib
from firefly.core.common import config
from firefly.core.enum import ObjectStatus
from firefly.dialogs.send_to import show_send_to_dialog
from firefly.dialogs.batch_ops import show_batch_ops_dialog

from firefly.base_module import BaseModule
from firefly.objects import asset_cache
from firefly.view import FireflyView
from firefly.qt import (
    Qt,
    QLineEdit,
    QAbstractItemView,
    QApplication,
    QPushButton,
    QHBoxLayout,
    QIcon,
    QLabel,
    QWidget,
    QAction,
    QMenu,
    QToolBar,
    QVBoxLayout,
    QMessageBox,
    QTabWidget,
    app_skin,
)

from .browser_model import BrowserModel


class SearchWidget(QLineEdit):
    def __init__(self, parent):
        super(QLineEdit, self).__init__()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.parent().load()
        elif event.key() == Qt.Key_Escape:
            self.line_edit.setText("")
        elif event.key() in [Qt.Key_Down, Qt.Key_Up]:
            self.parent().view.setFocus()
        QLineEdit.keyPressEvent(self, event)


class FireflyBrowserView(FireflyView):
    def __init__(self, parent):
        super(FireflyBrowserView, self).__init__(parent)
        self.current_page = 1
        self.page_count = 1
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.activated.connect(self.on_activate)
        self.setModel(BrowserModel(self))
        self.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

    def selectionChanged(self, selected, deselected):
        rows = []
        self.selected_objects = []

        tot_dur = 0
        for idx in self.selectionModel().selectedIndexes():
            row = idx.row()
            if row in rows:
                continue
            rows.append(row)
            obj = self.model().object_data[row]
            self.selected_objects.append(obj)
            if obj.object_type in ["asset", "item"]:
                tot_dur += obj.duration

        if self.selected_objects:
            self.main_window.focus(asset_cache[self.selected_objects[-1].id])
            if len(self.selected_objects) > 1 and tot_dur:
                logging.debug(
                    f"[BROWSER] {len(self.selected_objects)} objects selected. "
                    "Total duration {durstr}"
                )
        super(FireflyView, self).selectionChanged(selected, deselected)

    @property
    def current_order(self):
        try:
            return self.parent().search_query.get("order", "ctime desc").split(" ")
        except Exception:
            return ["ctime", "desc"]

    def on_header_clicked(self, index):
        old_order, old_trend = self.current_order
        value = self.model().header_data[index]
        if value == old_order:
            if old_trend == "asc":
                trend = "desc"
            else:
                trend = "asc"
        else:
            trend = "asc"
        self.parent().search_query["order"] = f"{value} {trend}"
        self.parent().load()

    def on_activate(self, mi):
        obj = self.model().object_data[mi.row()]
        key = self.model().header_data[mi.column()]
        val = obj.show(key)

        QApplication.clipboard().setText(str(val))
        logging.info(f'Copied "{val}" to clipboard')

    def set_page(self, current_page, page_count):
        self.current_page = current_page
        self.page_count = page_count
        if self.page_count > 1:
            self.parent().pager.show()
        else:
            self.parent().pager.hide()

        if self.current_page == 1:
            self.parent().pager.btn_prev.setEnabled(False)
        else:
            self.parent().pager.btn_prev.setEnabled(True)

        if self.current_page == page_count:
            self.parent().pager.btn_next.setEnabled(False)
        else:
            self.parent().pager.btn_next.setEnabled(True)

        self.parent().pager.info.setText(f"Page {current_page}")


class PagerButton(QPushButton):
    pass


class Pager(QWidget):
    def __init__(self, parent):
        layout = QHBoxLayout()
        super(Pager, self).__init__(parent)
        self._parent = parent

        self.btn_prev = PagerButton()
        self.btn_prev.setIcon(QIcon(pixlib["previous"]))
        self.btn_prev.clicked.connect(self.on_prev)
        layout.addWidget(self.btn_prev, 0)

        self.info = QLabel("Page 1")
        self.info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info, 1)

        self.btn_next = PagerButton()
        self.btn_next.setIcon(QIcon(pixlib["next"]))
        self.btn_next.clicked.connect(self.on_next)
        layout.addWidget(self.btn_next, 0)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def on_prev(self):
        if self._parent.view.current_page > 1:
            self._parent.view.current_page -= 1
            self._parent.load()

    def on_next(self):
        self._parent.view.current_page += 1
        self._parent.load()


class BrowserTab(QWidget):
    def __init__(self, parent, **kwargs):
        super(BrowserTab, self).__init__(parent)
        self._parent = parent
        self.loading = False
        self.title = False

        # Search query

        self.search_query = {
            "id_view": kwargs.get("id_view", min(config["views"])),
            "fulltext": kwargs.get("fulltext", ""),
            "order": kwargs.get("order", "ctime desc"),
            "conds": kwargs.get("conds", []),
        }

        # Layout

        self.search_box = SearchWidget(self)
        if self.search_query.get("fulltext"):
            self.search_box.setText(self.search_query["fulltext"])

        self.first_load = True
        self.view = FireflyBrowserView(self)
        self.view.horizontalHeader().sectionResized.connect(self.on_section_resize)
        self.view.horizontalHeader().sortIndicatorChanged.connect(
            self.on_section_resize
        )

        action_clear = QAction(QIcon(pixlib["cancel"]), "&Clear search query", parent)
        action_clear.triggered.connect(self.on_clear)

        self.action_search = QMenu("Views")
        self.action_search.setStyleSheet(app_skin)
        self.action_search.menuAction().setIcon(QIcon(pixlib["search"]))
        self.action_search.menuAction().triggered.connect(self.load)
        self.load_view_menu()

        action_copy = QAction("Copy result", self)
        action_copy.setShortcut("CTRL+SHIFT+C")
        action_copy.triggered.connect(self.on_copy_result)
        self.addAction(action_copy)

        toolbar = QToolBar(self)
        toolbar.addAction(action_clear)
        toolbar.addAction(self.action_search.menuAction())

        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(toolbar)

        self.pager = Pager(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(search_layout, 0)
        layout.addWidget(self.view, 1)
        layout.addWidget(self.pager, 0)
        self.setLayout(layout)

    def model(self):
        return self.view.model()

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
            config["views"].keys(), key=lambda k: config["views"][k]["position"]
        ):
            view = config["views"][id_view]
            if view.get("separator", False):
                self.action_search.addSeparator()
            action = QAction(view["title"], self)
            action.setCheckable(True)
            if i < 10:
                action.setShortcut(f"ALT+{i}")
            action.id_view = id_view
            action.triggered.connect(functools.partial(self.set_view, id_view))
            self.action_search.addAction(action)
            i += 1

    def on_section_resize(self, *args, **kwargs):
        if self.loading:
            return
        if "browser_view_sizes" not in self.app_state:
            self.app_state["browser_view_sizes"] = {}
        if "browser_default_sizes" not in self.app_state:
            self.app_state["browser_default_sizes"] = {}

        data = {}
        for i, h in enumerate(self.model().header_data):
            w = self.view.horizontalHeader().sectionSize(i)
            self.app_state["browser_default_sizes"][h] = w
            data[h] = w
        self.app_state["browser_view_sizes"][self.id_view] = data

    #
    # Do browse
    #

    def load(self, **kwargs):
        self.loading = True
        self.old_view = self.search_query.get("id_view", -1)
        search_string = self.search_box.text()
        self.search_query["fulltext"] = search_string
        self.search_query.update(kwargs)
        if self.search_query.get("id_view") != self.old_view:
            self.view.current_page = 1
        self.model().load(self.load_callback, **self.search_query)

    def load_callback(self):
        if self.first_load or self.id_view != self.old_view:
            view_state = self.app_state.get("browser_view_sizes", {}).get(
                self.id_view, {}
            )
            default_sizes = self.app_state.get("browser_defaut_sizes", {})
            for i, h in enumerate(self.model().header_data):
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
            for action in self.action_search.actions():
                if not hasattr(action, "id_view"):
                    continue
                if action.id_view == self.id_view:
                    action.setChecked(True)
                else:
                    action.setChecked(False)
            self.first_load = False

        self.loading = False
        self._parent.redraw_tabs()

    def on_clear(self):
        self.search_box.setText("")
        self.load(fulltext="")

    def set_view(self, id_view):
        self.search_query["conds"] = []
        self.title = False
        self.load(id_view=id_view)

    def contextMenuEvent(self, event):
        if not self.view.selected_objects:
            return
        menu = QMenu(self)
        objs = self.view.selected_objects

        states = set([obj["status"] for obj in objs])

        if states == set([ObjectStatus.TRASHED]):
            action_untrash = QAction("Untrash", self)
            action_untrash.setStatusTip("Take selected asset(s) from trash")
            action_untrash.triggered.connect(self.on_untrash)
            menu.addAction(action_untrash)

        if states == set([ObjectStatus.ARCHIVED]):
            action_unarchive = QAction("Unarchive", self)
            action_unarchive.setStatusTip("Take selected asset(s) from archive")
            action_unarchive.triggered.connect(self.on_unarchive)
            menu.addAction(action_unarchive)

        elif states.issubset(
            [ObjectStatus.ONLINE, ObjectStatus.CREATING, ObjectStatus.OFFLINE]
        ):
            action_move_to_trash = QAction("Move to trash", self)
            action_move_to_trash.setStatusTip("Move selected asset(s) to trash")
            action_move_to_trash.triggered.connect(self.on_trash)
            menu.addAction(action_move_to_trash)

            action_move_to_archive = QAction("Move to archive", self)
            action_move_to_archive.setStatusTip("Move selected asset(s) to archive")
            action_move_to_archive.triggered.connect(self.on_archive)
            menu.addAction(action_move_to_archive)

        action_reset = QAction("Reset", self)
        action_reset.setStatusTip("Reload asset metadata")
        action_reset.triggered.connect(self.on_reset)
        menu.addAction(action_reset)

        action_batch_ops = QAction("&Batch ops...", self)
        action_batch_ops.setStatusTip("Batch operations")
        action_batch_ops.triggered.connect(self.on_batch_ops)
        menu.addAction(action_batch_ops)

        if len(objs) == 1:
            menu.addSeparator()
            for link in config["folders"][objs[0]["id_folder"]].get("links", []):
                action_link = QAction(link["title"])
                action_link.triggered.connect(
                    functools.partial(self.link_exec, objs[0], **link)
                )
                menu.addAction(action_link)

        menu.addSeparator()

        action_send_to = QAction("&Send to...", self)
        action_send_to.setStatusTip("Create action for selected asset(s)")
        action_send_to.triggered.connect(self.on_send_to)
        menu.addAction(action_send_to)

        menu.exec_(event.globalPos())

    def link_exec(self, obj, **kwargs):
        param = kwargs["target_key"]
        value = obj[kwargs["source_key"]]
        self._parent.new_tab(
            obj["title"], id_view=kwargs["id_view"], conds=[f"'{param}' = '{value}'"]
        )
        self._parent.redraw_tabs()

    def on_send_to(self):
        objs = self.view.selected_objects
        if objs:
            show_send_to_dialog(objs)

    def on_batch_ops(self):
        objs = self.view.selected_objects
        if objs:
            if show_batch_ops_dialog(objs):
                self.load()

    def on_reset(self):
        objects = [
            obj.id
            for obj in self.view.selected_objects
            if obj["status"]
            not in [ObjectStatus.ARCHIVED, ObjectStatus.TRASHED, ObjectStatus.RESET]
        ]
        if not objects:
            return
        response = api.set(objects=objects, data={"status": ObjectStatus.RESET})
        if not response:
            return
        self.refresh_assets(*objects, request_data=True)

    def on_trash(self):
        objects = [
            obj.id
            for obj in self.view.selected_objects
            if obj["status"] not in [ObjectStatus.ARCHIVED, ObjectStatus.TRASHED]
        ]
        if not objects:
            return
        ret = QMessageBox.question(
            self,
            "Trash",
            f"Do you really want to trash {len(objects)} selected asset(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            response = api.set(objects=objects, data={"status": ObjectStatus.TRASHED})
        else:
            return
        if not response:
            logging.error("Unable to trash:\n\n" + response.message)
            return
        self.refresh_assets(*objects, request_data=True)

    def on_untrash(self):
        objects = [
            obj.id
            for obj in self.view.selected_objects
            if obj["status"] in [ObjectStatus.TRASHED]
        ]
        if not objects:
            return
        response = api.set(objects=objects, data={"status": ObjectStatus.CREATING})
        if not response:
            logging.error("Unable to untrash:\n\n" + response.message)
            return
        self.refresh_assets(*objects, request_data=True)

    def on_archive(self):
        objects = [
            obj.id
            for obj in self.view.selected_objects
            if obj["status"] not in [ObjectStatus.ARCHIVED, ObjectStatus.TRASHED]
        ]
        if not objects:
            return
        ret = QMessageBox.question(
            self,
            "Archive",
            f"Do you really want to move {len(objects)} selected asset(s) to archive?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            response = api.set(objects=objects, data={"status": ObjectStatus.ARCHIVED})
        else:
            return
        if not response:
            logging.error("Unable to archive:\n\n" + response.message)
            return
        self.refresh_assets(*objects, request_data=True)

    def on_unarchive(self):
        objects = [
            obj.id
            for obj in self.view.selected_objects
            if obj["status"] in [ObjectStatus.ARCHIVED]
        ]
        if not objects:
            return
        response = api.set(objects=objects, data={"status": ObjectStatus.RETRIEVING})
        if not response:
            logging.error("Unable to unarchive:\n\n" + response.message)
            return
        self.refresh_assets(*objects, request_data=True)

    def on_choose_columns(self):
        # TODO
        logging.error("Not implemented")

    def on_copy_result(self):
        result = ""
        for obj in self.view.selected_objects:
            result += "{}\n".format(
                "\t".join(
                    [obj.format_display(key) or "" for key in self.model().header_data]
                )
            )
        clipboard = QApplication.clipboard()
        clipboard.setText(result)

    def refresh_assets(self, *objects, request_data=False):
        if request_data:
            asset_cache.request([[aid, 0] for aid in objects])
        for row, obj in enumerate(self.model().object_data):
            if obj.id in objects:
                self.model().object_data[row] = asset_cache[obj.id]
                self.model().dataChanged.emit(
                    self.model().index(row, 0),
                    self.model().index(row, len(self.model().header_data) - 1),
                )

    def seismic_handler(self, message):
        pass  # No seismic message needed - refresh_assets method does the job


class BrowserModule(BaseModule):
    def __init__(self, parent):
        super(BrowserModule, self).__init__(parent)
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_switch)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

        tabscfg = self.app_state.get("browser_tabs", [])
        created_tabs = 0
        current_index = 0
        for tabcfg in tabscfg:
            try:
                if tabcfg["id_view"] not in config["views"]:
                    continue
                if tabcfg.get("active"):
                    current_index = self.tabs.count()
                try:
                    del tabcfg["active"]
                except KeyError:
                    pass
                title = False
                if tabcfg.get("title"):
                    title = tabcfg.get("title")
                try:
                    del tabcfg["title"]
                except KeyError:
                    pass

                self.new_tab(title, **tabcfg)
                created_tabs += 1
            except Exception:
                log_traceback()
                logging.warning("Unable to restore tab")
        if not created_tabs:
            self.new_tab()

        self.tabs.setCurrentIndex(current_index)

    def new_tab(self, title=False, **kwargs):
        if "id_view" not in kwargs:
            try:
                id_view = self.tabs.currentWidget().id_view
            except AttributeError:
                pass
            else:
                kwargs["id_view"] = id_view
        tab = BrowserTab(self, **kwargs)
        self.tabs.addTab(tab, "New tab")
        self.tabs.setCurrentIndex(self.tabs.indexOf(tab))
        tab.title = title
        tab.load()
        return tab

    @property
    def browsers(self):
        r = []
        for i in range(0, self.tabs.count()):
            r.append(self.tabs.widget(i))
        return r

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
            n = self.tabs.count() - 1
        else:
            n = cur - 1
        self.tabs.setCurrentIndex(n)

    def next_tab(self):
        cur = self.tabs.currentIndex()
        if cur == self.tabs.count() - 1:
            n = 0
        else:
            n = cur + 1
        self.tabs.setCurrentIndex(n)

    def on_tab_switch(self):
        browser = self.browsers[self.tabs.currentIndex()]
        sel = browser.view.selected_objects
        if sel:
            self.main_window.focus(sel[0])
        browser.search_box.setFocus()
        self.redraw_tabs()

    def load(self):
        for b in self.browsers:
            b.load()

    def redraw_tabs(self, *args, **kwargs):
        QApplication.processEvents()
        views = []
        for i, b in enumerate(self.browsers):
            id_view = b.id_view
            self.tabs.setTabText(i, b.title or config["views"][id_view]["title"])
            sq = copy.copy(b.search_query)
            if self.tabs.currentIndex() == i:
                sq["active"] = True
            if b.title:
                sq["title"] = b.title
            views.append(sq)
        self.app_state["browser_tabs"] = views

    def seismic_handler(self, message):
        for b in self.browsers:
            b.seismic_handler(message)

    def refresh_assets(self, *objects, request_data=False):
        for b in self.browsers:
            b.refresh_assets(*objects, request_data=request_data)
