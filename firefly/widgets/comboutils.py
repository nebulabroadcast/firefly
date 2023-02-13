__all__ = ["ComboMenuDelegate", "CheckComboBox"]


from firefly.qt import (
    Qt,
    QAbstractItemDelegate,
    QApplication,
    QStyle,
    QStyleOptionMenuItem,
    QBrush,
    QColor,
    QPixmap,
    QPalette,
    QIcon,
    QFontMetrics,
    QComboBox,
    QTimer,
    QStyleOptionComboBox,
    QStylePainter,
    QEvent,
)


class ComboMenuDelegate(QAbstractItemDelegate):
    def isSeparator(self, index):
        return str(index.data(Qt.ItemDataRole.AccessibleDescriptionRole)) == "separator"

    def paint(self, painter, option, index):
        menuopt = self._getMenuStyleOption(option, index)
        if option.widget is not None:
            style = option.widget.style()
        else:
            style = QApplication.style()
        style.drawControl(
            QStyle.ControlElement.CE_MenuItem, menuopt, painter, option.widget
        )

    def sizeHint(self, option, index):
        menuopt = self._getMenuStyleOption(option, index)
        if option.widget is not None:
            style = option.widget.style()
        else:
            style = QApplication.style()
        return style.sizeFromContents(
            QStyle.ContentsType.CT_MenuItem, menuopt, menuopt.rect.size(), option.widget
        )

    def _getMenuStyleOption(self, option, index):
        menuoption = QStyleOptionMenuItem()
        palette = option.palette.resolve(QApplication.palette("QMenu"))
        foreground = index.data(Qt.ItemDataRole.ForegroundRole)
        if isinstance(foreground, (QBrush, QColor, QPixmap)):
            foreground = QBrush(foreground)
            palette.setBrush(QPalette.ColorRole.Text, foreground)
            palette.setBrush(QPalette.ColorRole.ButtonText, foreground)
            palette.setBrush(QPalette.ColorRole.WindowText, foreground)

        background = index.data(Qt.ItemDataRole.BackgroundRole)
        if isinstance(background, (QBrush, QColor, QPixmap)):
            background = QBrush(background)
            palette.setBrush(QPalette.Background, background)

        menuoption.palette = palette

        decoration = index.data(Qt.ItemDataRole.DecorationRole)
        if isinstance(decoration, QIcon):
            menuoption.icon = decoration

        if self.isSeparator(index):
            menuoption.menuItemType = QStyleOptionMenuItem.MenuItemType.Separator
        else:
            menuoption.menuItemType = QStyleOptionMenuItem.MenuItemType.Normal

        if index.flags() & Qt.ItemFlag.ItemIsUserCheckable:
            menuoption.checkType = QStyleOptionMenuItem.CheckType.NonExclusive
        else:
            menuoption.checkType = QStyleOptionMenuItem.CheckType.NotCheckable

        check = index.data(Qt.ItemDataRole.CheckStateRole)
        menuoption.checked = check == Qt.CheckState.Checked

        if option.widget is not None:
            menuoption.font = option.widget.font()
        else:
            menuoption.font = QApplication.font("QMenu")

        if index.data(Qt.ItemDataRole.FontRole):
            menuoption.font = index.data(Qt.ItemDataRole.FontRole)

        menuoption.maxIconWidth = option.decorationSize.width() + 4
        menuoption.rect = option.rect
        menuoption.menuRect = option.rect

        idt = index.data(Qt.ItemDataRole.UserRole)

        if idt is not None:
            idt = int(idt)
            menuoption.rect.adjust(idt * 24, 0, 0, 0)

        menuoption.menuHasCheckableItems = True
        menuoption.tabWidth = 0
        display = str(index.data(Qt.ItemDataRole.DisplayRole))
        menuoption.text = display

        menuoption.fontMetrics = QFontMetrics(menuoption.font)
        state = option.state & (
            QStyle.StateFlag.State_MouseOver
            | QStyle.StateFlag.State_Selected
            | QStyle.StateFlag.State_Active
        )

        if index.flags() & Qt.ItemFlag.ItemIsEnabled:
            state = state | QStyle.StateFlag.State_Enabled
            menuoption.palette.setCurrentColorGroup(QPalette.ColorGroup.Active)
        else:
            state = state & ~QStyle.StateFlag.State_Enabled
            menuoption.palette.setCurrentColorGroup(QPalette.ColorGroup.Disabled)

        if menuoption.checked:
            state = state | QStyle.StateFlag.State_On
        else:
            state = state | QStyle.StateFlag.State_Off

        menuoption.state = state
        return menuoption


class CheckComboBox(QComboBox):
    def __init__(self, parent=None, placeholderText="", separator=", ", **kwargs):
        super(CheckComboBox, self).__init__(parent, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.__popupIsShown = False
        self.__supressPopupHide = False
        self.__blockMouseReleaseTimer = QTimer(self, singleShot=True)
        self.__initialMousePos = None
        self.__separator = separator
        self.__placeholderText = placeholderText
        self.__updateItemDelegate()

    def mousePressEvent(self, event):
        """Reimplemented."""
        self.__popupIsShown = False
        super(CheckComboBox, self).mousePressEvent(event)
        if self.__popupIsShown:
            self.__initialMousePos = self.mapToGlobal(event.pos())
            self.__blockMouseReleaseTimer.start(QApplication.doubleClickInterval())

    def changeEvent(self, event):
        """Reimplemented."""
        if event.type() == QEvent.Type.StyleChange:
            self.__updateItemDelegate()
        super(CheckComboBox, self).changeEvent(event)

    def showPopup(self):
        """Reimplemented."""
        super(CheckComboBox, self).showPopup()
        view = self.view()
        view.installEventFilter(self)
        view.viewport().installEventFilter(self)
        self.__popupIsShown = True

    def hidePopup(self):
        """Reimplemented."""
        self.view().removeEventFilter(self)
        self.view().viewport().removeEventFilter(self)
        self.__popupIsShown = False
        self.__initialMousePos = None
        super(CheckComboBox, self).hidePopup()
        self.view().clearFocus()

    def eventFilter(self, obj, event):
        """Reimplemented."""
        if (
            self.__popupIsShown
            and event.type() == QEvent.Type.MouseMove
            and self.view().isVisible()
            and self.__initialMousePos is not None
        ):
            diff = obj.mapToGlobal(event.pos()) - self.__initialMousePos
            if diff.manhattanLength() > 9 and self.__blockMouseReleaseTimer.isActive():
                self.__blockMouseReleaseTimer.stop()
            # pass through

        if (
            self.__popupIsShown
            and event.type() == QEvent.Type.MouseButtonRelease
            and self.view().isVisible()
            and self.view().rect().contains(event.pos())
            and self.view().currentIndex().isValid()
            and self.view().currentIndex().flags() & Qt.ItemFlag.ItemIsSelectable
            and self.view().currentIndex().flags() & Qt.ItemFlag.ItemIsEnabled
            and self.view().currentIndex().flags() & Qt.ItemFlag.ItemIsUserCheckable
            and self.view().visualRect(self.view().currentIndex()).contains(event.pos())
            and not self.__blockMouseReleaseTimer.isActive()
        ):
            model = self.model()
            index = self.view().currentIndex()
            state = model.data(index, Qt.ItemDataRole.CheckStateRole)
            model.setData(
                index,
                Qt.CheckState.Checked
                if state == Qt.CheckState.Unchecked
                else Qt.CheckState.Unchecked,
                Qt.ItemDataRole.CheckStateRole,
            )
            self.view().update(index)
            return True

        if self.__popupIsShown and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Space:
                # toogle the current items check state
                model = self.model()
                index = self.view().currentIndex()
                flags = model.flags(index)
                state = model.data(index, Qt.ItemDataRole.CheckStateRole)
                if (
                    flags & Qt.ItemFlag.ItemIsUserCheckable
                    and flags & Qt.ItemIsTristate
                ):
                    state = Qt.CheckState((int(state) + 1) % 3)
                elif flags & Qt.ItemFlag.ItemIsUserCheckable:
                    state = (
                        Qt.CheckState.Checked
                        if state != Qt.CheckState.Checked
                        else Qt.CheckState.Unchecked
                    )
                model.setData(index, state, Qt.ItemDataRole.CheckStateRole)
                return True
            # TODO: handle Qt.Key.Key_Enter, Key_Return?

        return super(CheckComboBox, self).eventFilter(obj, event)

    def paintEvent(self, event):
        """Reimplemented."""
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
        # draw the icon and text
        checked = self.checkedIndices()
        if checked:
            items = [self.itemText(i) for i in checked]
            option.currentText = self.__separator.join(items)
        else:
            option.currentText = self.__placeholderText
            option.palette.setCurrentColorGroup(QPalette.ColorGroup.Disabled)

        option.currentIcon = QIcon()
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)

    def itemCheckState(self, index):
        state = self.itemData(index, role=Qt.ItemDataRole.CheckStateRole)
        if isinstance(state, int):
            return Qt.CheckState(state)
        else:
            return Qt.CheckState.Unchecked

    def setItemCheckState(self, index, state):
        state = Qt.CheckState.Checked if state else Qt.CheckState.Unchecked
        self.setItemData(index, state, Qt.ItemDataRole.CheckStateRole)

    def checkedIndices(self):
        return [i for i in range(self.count()) if self.itemCheckState(i)]

    def setPlaceholderText(self, text):
        if self.__placeholderText != text:
            self.__placeholderText = text
            self.update()

    def placeholderText(self):
        return self.__placeholderText

    def wheelEvent(self, event):
        """Reimplemented."""
        event.ignore()

    def keyPressEvent(self, event):
        """Reimplemented."""
        # Override the default QComboBox behavior
        if (
            event.key() == Qt.Key.Key_Down
            and event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            self.showPopup()
            return

        ignored = {
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_PageDown,
            Qt.Key.Key_PageUp,
            Qt.Key.Key_Home,
            Qt.Key.Key_End,
        }

        if event.key() in ignored:
            event.ignore()
            return

        super(CheckComboBox, self).keyPressEvent(event)

    def __updateItemDelegate(self):
        opt = QStyleOptionComboBox()
        opt.initFrom(self)
        delegate = ComboMenuDelegate(self)
        self.setItemDelegate(delegate)
