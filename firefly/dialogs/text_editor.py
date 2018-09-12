from firefly import *
from firefly.syntaxhl import *

class TextWidget(QTextEdit):
    def __init__(self, parent, syntax=False):
        super(TextWidget, self).__init__(parent)
        self.syntax = syntax

        if syntax == "python":
            hl = PythonHL(self)
            #option = self.document().defaultTextOption()
            #option.setFlags(option.flags() | QTextOption.ShowTabsAndSpaces);
            #self.document().setDefaultTextOption(option)

    def keyPressEvent(self,  event):
        if event.key() == Qt.Key_Return:
            cursor = self.textCursor()
            txt = cursor.block().text()
            trail_spaces = (len(txt) - len(txt.lstrip()))

            if self.syntax == "python":
                words = txt.lstrip().split()
                if words and words[0] in ["if", "for", "while", "def", "class", "elif", "else", "try", "except", "finally"]:
                    trail_spaces += 4
                if words and words[0] in ["return", "pass", "break"]:
                    trail_spaces = max(trail_spaces-4, 0)

            cursor.insertText("\n" + " "*trail_spaces)
            return

        elif event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText("    ")
            return
        self.parent().status("")
        QTextEdit.keyPressEvent(self,  event)


def editor_toolbar(wnd):
    toolbar = QToolBar(wnd)
    toolbar.setMovable(False)
    toolbar.setFloatable(False)

    toolbar.addSeparator()

    action_accept = QAction(QIcon(pix_lib["accept"]), 'Accept changes', wnd)
    action_accept.setShortcut('CTRL+S')
    action_accept.triggered.connect(wnd.on_accept)
    toolbar.addAction(action_accept)

    action_cancel = QAction(QIcon(pix_lib["cancel"]), 'Cancel', wnd)
    action_cancel.setShortcut('ESC')
    action_cancel.triggered.connect(wnd.on_cancel)
    toolbar.addAction(action_cancel)

    return toolbar



class TextEditorDialog(QDialog):
    def __init__(self, default, index=False, syntax=False):
        super(TextEditor, self).__init__()

        self.setWindowTitle('Firefly text editor')
        self.setModal(True)

        self.toolbar = editor_toolbar(self)
        self.statusbar = QStatusBar()

        self.edit = TextWidget(self, syntax)
        self.default = default
        self.setText(default)

        self.index = index

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        layout.addWidget(self.toolbar, 1)
        layout.addWidget(self.edit, 2)
        layout.addWidget(self.statusbar, 0)

        self.setStyleSheet(base_css)
        self.setLayout(layout)
        self.resize(640,640)

        self.show()
        self.raise_()
        self.edit.activateWindow()
        self.edit.setFocus()
        self.status("Press ESC to discard changes or CTRL+S to save and close")


    def status(self, message, message_type=INFO):
        if message_type > DEBUG:
            self.statusbar.showMessage(message)

    def on_accept(self):
        if self.index:
            self.index.model().setData(self.index,self.toPlainText())
        self.close()

    def on_cancel(self):
        self.close()

    def setText(self,text):
        self.edit.setText(text)

    def toPlainText(self):
        return self.edit.toPlainText()
