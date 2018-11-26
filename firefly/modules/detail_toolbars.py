import functools

from firefly import *

def preview_toolbar(wnd):
    toolbar = QToolBar(wnd)

    action_poster = QMenu("Set poster", wnd)
    action_poster.menuAction().setIcon(QIcon(pix_lib["set-poster"]))
    action_poster.menuAction().triggered.connect(wnd.set_poster)
    action_poster.menuAction().setStatusTip('Set poster frame')

    action_poster_set = QAction("Set poster", wnd)
    action_poster_set.triggered.connect(wnd.set_poster)
    action_poster.addAction(action_poster_set)

    action_poster_goto = QAction("Go to poster", wnd)
    action_poster_goto.triggered.connect(wnd.go_to_poster)
    action_poster.addAction(action_poster_goto)

    toolbar.addAction(action_poster.menuAction())

    action_save_marks = QAction(QIcon(pix_lib["save-marks"]), 'Save marks', wnd)
    action_save_marks.setStatusTip('Save marks')
    action_save_marks.triggered.connect(wnd.save_marks)
    toolbar.addAction(action_save_marks)

#TODO
#    action_restore_marks = QAction(QIcon(pix_lib["restore-marks"]), 'Restore marks', wnd)
#    action_restore_marks.setStatusTip('Restore marks')
#    action_restore_marks.triggered.connect(wnd.restore_marks)
#    toolbar.addAction(action_restore_marks)

    action_create_subclip = QAction(QIcon(pix_lib["create-subclip"]), 'Create subclip', wnd)
    action_create_subclip.setStatusTip('Create subclip')
    action_create_subclip.triggered.connect(wnd.create_subclip)
    toolbar.addAction(action_create_subclip)

    action_manage_subclips = QAction(QIcon(pix_lib["manage-subclips"]), 'Manage subclips', wnd)
    action_manage_subclips.setStatusTip('Manage subclips')
    action_manage_subclips.triggered.connect(wnd.manage_subclips)
    toolbar.addAction(action_manage_subclips)

    return toolbar



def detail_toolbar(wnd):
    toolbar = QToolBar(wnd)

    fdata = []
    for id_folder in sorted(config["folders"].keys()):
        fdata.append([id_folder, config["folders"][id_folder]["title"]])

    wnd.folder_select = FireflySelect(wnd, data=fdata)
    for i, fd in enumerate(fdata):
        wnd.folder_select.setItemIcon(i, QIcon(pix_lib["folder_"+str(fd[0])]))
    wnd.folder_select.currentIndexChanged.connect(wnd.on_folder_changed)
    wnd.folder_select.setEnabled(False)
    toolbar.addWidget(wnd.folder_select)

    toolbar.addSeparator()

    wnd.duration =  FireflyTimecode(wnd)
    toolbar.addWidget(wnd.duration)

    toolbar.addSeparator()

    wnd.action_approve = QAction(QIcon(pix_lib["qc_approved"]),'Approve', wnd)
    wnd.action_approve.setShortcut('Y')
    wnd.action_approve.triggered.connect(functools.partial(wnd.on_set_qc, 4))
    wnd.action_approve.setEnabled(False)
    toolbar.addAction(wnd.action_approve)

    wnd.action_qc_reset = QAction(QIcon(pix_lib["qc_new"]),'QC Reset', wnd)
    wnd.action_qc_reset.setShortcut('T')
    wnd.action_qc_reset.triggered.connect(functools.partial(wnd.on_set_qc, 0))
    wnd.action_qc_reset.setEnabled(False)
    toolbar.addAction(wnd.action_qc_reset)

    wnd.action_reject = QAction(QIcon(pix_lib["qc_rejected"]),'Reject', wnd)
    wnd.action_reject.setShortcut('U')
    wnd.action_reject.triggered.connect(functools.partial(wnd.on_set_qc, 3))
    wnd.action_reject.setEnabled(False)
    toolbar.addAction(wnd.action_reject)

    toolbar.addWidget(ToolBarStretcher(wnd))

    wnd.action_revert = QAction(QIcon(pix_lib["cancel"]), '&Revert changes', wnd)
    wnd.action_revert.setStatusTip('Revert changes')
    wnd.action_revert.triggered.connect(wnd.on_revert)
    toolbar.addAction(wnd.action_revert)

    wnd.action_apply = QAction(QIcon(pix_lib["accept"]), '&Apply changes', wnd)
    wnd.action_apply.setShortcut('Ctrl+S')
    wnd.action_apply.setStatusTip('Apply changes')
    wnd.action_apply.triggered.connect(wnd.on_apply)
    toolbar.addAction(wnd.action_apply)

    return toolbar
