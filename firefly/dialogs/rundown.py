from firefly import *

__all__ = ["PlaceholderDialog", "SubclipSelectDialog", "trim_dialog"]


class PlaceholderDialog(QDialog):
    def __init__(self,  parent, meta):
        super(PlaceholderDialog, self).__init__(parent)
        self.setWindowTitle("Rundown placeholder")
        item_role = meta.get("item_role", "placeholder")

        self.ok = False

        keys = []
        for k in ["title", "subtitle", "description", "color", "duration"]: #TODO
            if k in meta:
                keys.append([k, {"default": meta[k]}])

        self.form = MetaEditor(parent, keys)
        for k in keys:
            if meta_types[k[0]]["class"] == SELECT:
                self.form.inputs[k[0]].auto_data(meta_types[k[0]])
            k = k[0]
            self.form[k] = meta[k]

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.on_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.form, 1)
        layout.addWidget(buttons, 0)
        self.setLayout(layout)

        self.setModal(True)
        self.setMinimumWidth(400)

    @property
    def meta(self):
        return self.form.meta

    def on_cancel(self):
        self.close()

    def on_accept(self):
        self.ok = True
        self.close()


class SubclipSelectDialog(QDialog):
    def __init__(self,  parent, asset):
        super(SubclipSelectDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowTitle(f"Select {asset} subclip to use")
        self.ok = False
        self.asset = asset
        self.subclips = asset.meta.get("subclips", [])
        self.subclips.sort(key=lambda x: x["mark_in"])

        layout = QVBoxLayout()

        btn = QPushButton("Entire clip")
        btn.clicked.connect(functools.partial(self.on_submit, -1 ))
        layout.addWidget(btn)

        btn = QPushButton("All subclips")
        btn.clicked.connect(functools.partial(self.on_submit, -2 ))
        layout.addWidget(btn)

        for i, subclip in enumerate(self.subclips):
            btn = QPushButton("[{} - {}]  :  {}".format(
                    s2tc(subclip["mark_in"]),
                    s2tc(subclip["mark_out"]),
                    subclip["title"],
                ))
            btn.setStyleSheet("font: monospace; text-align: left;")
            btn.clicked.connect(functools.partial(self.on_submit, i))
            layout.addWidget(btn)

        self.setLayout(layout)


    def on_submit(self, subclip):
        self.result = []

        if subclip == -1:
            self.result = [{
                    "mark_in" : self.asset["mark_in"],
                    "mark_out" : self.asset["mark_out"],
                }]

        elif subclip == -2:
            for sdata in self.subclips:
                self.result.append({
                        "mark_in" : sdata["mark_in"],
                        "mark_out" : sdata["mark_out"],
                        "title" : "{} ({})".format(self.asset["title"], sdata["title"])
                    })

        elif subclip >= 0:
            self.result = [{
                    "mark_in" : self.subclips[subclip]["mark_in"],
                    "mark_out" : self.subclips[subclip]["mark_out"],
                    "title" : "{} ({})".format(self.asset["title"], self.subclips[subclip]["title"])
                }]
        self.ok = True
        self.close()



class TrimDialog(QDialog):
    def __init__(self,  parent, item):
        super(TrimDialog, self).__init__(parent)
        self.setWindowTitle("Trim {}".format(item))

        self.ok = False
        self.item = item

        keys = [
                ["mark_in", {}],
                ["mark_out", {}],
            ]

        self.form = MetaEditor(parent, keys)
        for k,s in keys:
            self.form[k] = item[k]

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.on_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.form, 1)
        layout.addWidget(buttons, 0)
        self.setLayout(layout)

        self.setModal(True)
        self.setMinimumWidth(400)

    @property
    def meta(self):
        return self.form.meta

    def on_cancel(self):
        self.close()

    def on_accept(self):
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        response = api.set(
                object_type="item",
                objects=[self.item.id],
                data={
                        "mark_in" : self.form["mark_in"],
                        "mark_out" : self.form["mark_out"]
                    }

            )
        QApplication.restoreOverrideCursor()
        if not response:
            logging.error(response.message)
        self.close()

def trim_dialog(item):
    dlg = TrimDialog(None, item)
    dlg.exec_()
