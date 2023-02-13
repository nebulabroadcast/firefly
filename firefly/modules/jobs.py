import functools

from firefly.base_module import BaseModule
from firefly.widgets import ToolBarStretcher
from firefly.qt import (
    Qt,
    QLineEdit,
    QToolBar,
    QPushButton,
    QVBoxLayout,
)

from .jobs_model import FireflyJobsView


class SearchWidget(QLineEdit):
    def __init__(self, parent):
        super(QLineEdit, self).__init__()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.parent().parent().load()
        elif event.key() == Qt.Key.Key_Escape:
            self.line_edit.setText("")
        elif event.key() == Qt.Key.Key_Down:
            self.parent().parent().view.setFocus()
        QLineEdit.keyPressEvent(self, event)


class JobsModule(BaseModule):
    def __init__(self, parent):
        super(JobsModule, self).__init__(parent)

        self.view = FireflyJobsView(self)

        toolbar = QToolBar()

        btn_active = QPushButton("ACTIVE")
        btn_active.setCheckable(True)
        btn_active.setChecked(True)
        btn_active.setAutoExclusive(True)
        btn_active.clicked.connect(functools.partial(self.set_view, "active"))
        toolbar.addWidget(btn_active)

        btn_finished = QPushButton("FINISHED")
        btn_finished.setCheckable(True)
        btn_finished.setAutoExclusive(True)
        btn_finished.clicked.connect(functools.partial(self.set_view, "finished"))
        toolbar.addWidget(btn_finished)

        btn_failed = QPushButton("FAILED")
        btn_failed.setCheckable(True)
        btn_failed.setAutoExclusive(True)
        btn_failed.clicked.connect(functools.partial(self.set_view, "failed"))
        toolbar.addWidget(btn_failed)

        toolbar.addWidget(ToolBarStretcher(self))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.view, 1)
        self.setLayout(layout)
        self.set_view("active")

    @property
    def model(self):
        return self.view.model

    def load(self, **kwargs):
        self.view.model.load(**kwargs)

    def set_view(self, id_view="active"):
        self.id_view = id_view
        self.load(view=id_view)

    def seismic_handler(self, message):
        if self.main_window.current_module != self.main_window.jobs:
            return
        if self.id_view != "active":
            return

        d = message.data
        do_reload = False
        for i, row in enumerate(self.view.model.object_data):
            if row["id"] == d.get("id", False):
                row["message"] = d.get("message", "")
                row["progress"] = d.get("progress", 0)
                self.view.model.dataChanged.emit(
                    self.view.model.index(i, 0),
                    self.view.model.index(i, len(self.view.model.header_data) - 1),
                )
                if row["status"] != d.get("status", False):
                    do_reload = True
                break
        else:
            do_reload = True

        if do_reload:
            self.view.model.load()
