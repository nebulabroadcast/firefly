import math
import functools

from firefly import *

from .jobs_model import *

class SearchWidget(QLineEdit):
    def __init__(self, parent):
        super(QLineEdit, self).__init__()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return,Qt.Key_Enter]:
            self.parent().parent().load()
        elif event.key() == Qt.Key_Escape:
            self.line_edit.setText("")
        elif event.key() == Qt.Key_Down:
            self.parent().parent().view.setFocus()
        QLineEdit.keyPressEvent(self, event)




class JobsModule(BaseModule):
    def __init__(self, parent):
        super(JobsModule, self).__init__(parent)
        self.search_query = {}

        self.view = FireflyJobsView(self)

        #self.search_box = SearchWidget(self)
        #action_clear = QAction(QIcon(pix_lib["cancel"]), '&Clear search query', parent)
        #action_clear.triggered.connect(self.on_clear)

        self.action_search = QMenu("Views")
        self.action_search.menuAction().setIcon(QIcon(pix_lib["search"]))
        self.action_search.menuAction().triggered.connect(self.load)
        self.load_view_menu()

        toolbar = QToolBar()
        toolbar.addWidget(ToolBarStretcher(self))
        #toolbar.addWidget(self.search_box)
        #toolbar.addAction(action_clear)
        toolbar.addAction(self.action_search.menuAction())

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.view, 1)
        self.setLayout(layout)
        self.set_view("active")

    def load_view_menu(self):
        for title, status in [
                    ["Active", "active"],
                    ["Finished", "finished"],
                    ["Failed", "failed"],
                ]:
            action = QAction(title, self, checkable=True)
            action.id_view = status
            action.triggered.connect(functools.partial(self.set_view, status))
            self.action_search.addAction(action)

    @property
    def model(self):
        return self.view.model

#
# Do browse
#

    def load(self, **kwargs):
        self.view.model.load(**kwargs)

    def on_clear(self):
        self.search_box.setText("")
        self.load(fulltext="")

    def set_view(self, id_view="active"):
        self.id_view = id_view
        self.load(view=id_view)
        for action in self.action_search.actions():
            if not hasattr(action, "id_view"):
                continue
            if action.id_view == id_view:
                action.setChecked(True)
            else:
                action.setChecked(False)

    def contextMenuEvent(self, event):
        return

        if not self.view.selected_objects:
            return
        menu = QMenu(self)

        statuses = [obj["status"] for obj in self.view.selected_objects ]

        if len(statuses) == 1 and statuses[0] == TRASHED:
            action_untrash = QAction('Untrash', self)
            action_untrash.setStatusTip('Take selected asset(s) from trash')
            action_untrash.triggered.connect(self.on_untrash)
            menu.addAction(action_untrash)
        else:
            action_move_to_trash = QAction('Move to trash', self)
            action_move_to_trash.setStatusTip('Move selected asset(s) to trash')
            action_move_to_trash.triggered.connect(self.on_trash)
            menu.addAction(action_move_to_trash)

        if len(statuses) == 1 and statuses[0] == ARCHIVED:
            action_unarchive = QAction('Unarchive', self)
            action_unarchive.setStatusTip('Take selected asset(s) from archive')
            action_unarchive.triggered.connect(self.on_unarchive)
            menu.addAction(action_unarchive)
        else:
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

        menu.addSeparator()

        action_columns = QAction('Choose columns', self)
        action_columns.setStatusTip('Choose header columns')
        action_columns.triggered.connect(self.on_choose_columns)
        menu.addAction(action_columns)

        menu.exec_(event.globalPos())



    def seismic_handler(self, message):
        if self.main_window.current_module != self.main_window.jobs:
            return

        if self.id_view != "active":
            return

        d = message.data

        do_reload = False
        for row in self.view.model.object_data:
            if row["id"] == d.get("id", False):
                #TODO: emit change row instead reset model
                self.view.model.beginResetModel()
                row["message"] = d["message"]
                row["progress"] = d["progress"]
                self.view.model.endResetModel()
                if row["status"] != d.get("status", False):
                    do_reload = True
                break
        else:
            do_reload = True

        if do_reload:
            self.view.model.load()
