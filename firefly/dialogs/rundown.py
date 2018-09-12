from firefly import *

__all__ = ["PlaceholderDialog", "SubclipSelectDialog"]


class PlaceholderDialog(QDialog):
    def __init__(self,  parent, meta):
        super(PlaceholderDialog, self).__init__(parent)
        self.setWindowTitle("Rundown placeholder")
        item_role = meta.get("item_role", "placeholder")

        self.ok = False

        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.addWidget(ToolBarStretcher(toolbar))

        action_accept = QAction(QIcon(pix_lib["accept"]), 'Accept changes', self)
        action_accept.setShortcut('Ctrl+S')
        action_accept.triggered.connect(self.on_accept)
        toolbar.addAction(action_accept)

        #keys =  [[key, {"default":default}] for key, default in ITEM_ROLES[item_role]]
        keys = []
        for k in ["title", "subtitle", "description", "color", "duration"]: #TODO
            if k in meta:
                keys.append([k, {"default": meta[k]}])


        self.form = MetaEditor(parent, keys)
        for k in keys:
            k = k[0]
            self.form[k] = meta[k]


        layout = QVBoxLayout()
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.form, 1)
        self.setLayout(layout)

        self.setModal(True)
        self.setMinimumWidth(400)

    @property
    def meta(self):
        return self.form.meta

    def on_accept(self):
        self.ok = True
        self.close()



class SubclipSelectDialog(QDialog):
    def __init__(self,  parent, asset):
        super(SubclipSelectDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Select {} subclip to use".format(asset))
        self.ok = False

        layout = QVBoxLayout()

        btn = QPushButton("Entire clip")
        btn.clicked.connect(functools.partial(self.on_submit, "", [asset["mark_in"],asset["mark_out"]]))
        layout.addWidget(btn)

        subclips = asset.meta.get("subclips", {})
        for subclip in sorted(subclips):
            marks = subclips[subclip]
            btn = QPushButton(subclip)
            btn.clicked.connect(functools.partial(self.on_submit, subclip, marks))
            layout.addWidget(btn)

        self.setLayout(layout)


    def on_submit(self, clip, marks):
        self.marks = [float(mark) for mark in marks]
        self.clip = clip
        self.ok = True
        self.close()
