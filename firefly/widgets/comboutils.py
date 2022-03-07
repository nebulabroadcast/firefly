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
        return str(index.data(Qt.AccessibleDescriptionRole)) == "separator"

    def paint(self, painter, option, index):
        menuopt = self._getMenuStyleOption(option, index)
        if option.widget is not None:
            style = option.widget.style()
        else:
            style = QApplication.style()
        style.drawControl(QStyle.CE_MenuItem, menuopt, painter, option.widget)

    def sizeHint(self, option, index):
        menuopt = self._getMenuStyleOption(option, index)
        if option.widget is not None:
            style = option.widget.style()
        else:
            style = QApplication.style()
        return style.sizeFromContents(
            QStyle.CT_MenuItem, menuopt, menuopt.rect.size(), option.widget
        )

    def _getMenuStyleOption(self, option, index):
        menuoption = QStyleOptionMenuItem()
        palette = option.palette.resolve(QApplication.palette("QMenu"))
        foreground = index.data(Qt.ForegroundRole)
        if isinstance(foreground, (QBrush, QColor, QPixmap)):
            foreground = QBrush(foreground)
            palette.setBrush(QPalette.Text, foreground)
            palette.setBrush(QPalette.ButtonText, foreground)
            palette.setBrush(QPalette.WindowText, foreground)

        background = index.data(Qt.BackgroundRole)
        if isinstance(background, (QBrush, QColor, QPixmap)):
            background = QBrush(background)
            palette.setBrush(QPalette.Background, background)

        menuoption.palette = palette

        decoration = index.data(Qt.DecorationRole)
        if isinstance(decoration, QIcon):
            menuoption.icon = decoration

        if self.isSeparator(index):
            menuoption.menuItemType = QStyleOptionMenuItem.Separator
        else:
            menuoption.menuItemType = QStyleOptionMenuItem.Normal

        if index.flags() & Qt.ItemIsUserCheckable:
            menuoption.checkType = QStyleOptionMenuItem.NonExclusive
        else:
            menuoption.checkType = QStyleOptionMenuItem.NotCheckable

        check = index.data(Qt.CheckStateRole)
        menuoption.checked = check == Qt.Checked

        if option.widget is not None:
            menuoption.font = option.widget.font()
        else:
            menuoption.font = QApplication.font("QMenu")

        if index.data(Qt.FontRole):
            menuoption.font = index.data(Qt.FontRole)

        menuoption.maxIconWidth = option.decorationSize.width() + 4
        menuoption.rect = option.rect
        menuoption.menuRect = option.rect

        idt = index.data(Qt.UserRole)

        if idt is not None:
            idt = int(idt)
            menuoption.rect.adjust(idt * 16, 0, 0, 0)

        menuoption.menuHasCheckableItems = True
        menuoption.tabWidth = 0
        display = str(index.data(Qt.DisplayRole))
        menuoption.text = display

        menuoption.fontMetrics = QFontMetrics(menuoption.font)
        state = option.state & (
            QStyle.State_MouseOver | QStyle.State_Selected | QStyle.State_Active
        )

        if index.flags() & Qt.ItemIsEnabled:
            state = state | QStyle.State_Enabled
            menuoption.palette.setCurrentColorGroup(QPalette.Active)
        else:
            state = state & ~QStyle.State_Enabled
            menuoption.palette.setCurrentColorGroup(QPalette.Disabled)

        if menuoption.checked:
            state = state | QStyle.State_On
        else:
            state = state | QStyle.State_Off

        menuoption.state = state
        return menuoption


class CheckComboBox(QComboBox):
    def __init__(self, parent=None, placeholderText="", separator=", ", **kwargs):
        super(CheckComboBox, self).__init__(parent, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

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
        if event.type() == QEvent.StyleChange:
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
            and event.type() == QEvent.MouseMove
            and self.view().isVisible()
            and self.__initialMousePos is not None
        ):
            diff = obj.mapToGlobal(event.pos()) - self.__initialMousePos
            if diff.manhattanLength() > 9 and self.__blockMouseReleaseTimer.isActive():
                self.__blockMouseReleaseTimer.stop()
            # pass through

        if (
            self.__popupIsShown
            and event.type() == QEvent.MouseButtonRelease
            and self.view().isVisible()
            and self.view().rect().contains(event.pos())
            and self.view().currentIndex().isValid()
            and self.view().currentIndex().flags() & Qt.ItemIsSelectable
            and self.view().currentIndex().flags() & Qt.ItemIsEnabled
            and self.view().currentIndex().flags() & Qt.ItemIsUserCheckable
            and self.view().visualRect(self.view().currentIndex()).contains(event.pos())
            and not self.__blockMouseReleaseTimer.isActive()
        ):
            model = self.model()
            index = self.view().currentIndex()
            state = model.data(index, Qt.CheckStateRole)
            model.setData(
                index,
                Qt.Checked if state == Qt.Unchecked else Qt.Unchecked,
                Qt.CheckStateRole,
            )
            self.view().update(index)
            return True

        if self.__popupIsShown and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Space:
                # toogle the current items check state
                model = self.model()
                index = self.view().currentIndex()
                flags = model.flags(index)
                state = model.data(index, Qt.CheckStateRole)
                if flags & Qt.ItemIsUserCheckable and flags & Qt.ItemIsTristate:
                    state = Qt.CheckState((int(state) + 1) % 3)
                elif flags & Qt.ItemIsUserCheckable:
                    state = Qt.Checked if state != Qt.Checked else Qt.Unchecked
                model.setData(index, state, Qt.CheckStateRole)
                return True
            # TODO: handle Qt.Key_Enter, Key_Return?

        return super(CheckComboBox, self).eventFilter(obj, event)

    def paintEvent(self, event):
        """Reimplemented."""
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        painter.drawComplexControl(QStyle.CC_ComboBox, option)
        # draw the icon and text
        checked = self.checkedIndices()
        if checked:
            items = [self.itemText(i) for i in checked]
            option.currentText = self.__separator.join(items)
        else:
            option.currentText = self.__placeholderText
            option.palette.setCurrentColorGroup(QPalette.Disabled)

        option.currentIcon = QIcon()
        painter.drawControl(QStyle.CE_ComboBoxLabel, option)

    def itemCheckState(self, index):
        state = self.itemData(index, role=Qt.CheckStateRole)
        if isinstance(state, int):
            return Qt.CheckState(state)
        else:
            return Qt.Unchecked

    def setItemCheckState(self, index, state):
        state = Qt.Checked if state else Qt.Unchecked
        self.setItemData(index, state, Qt.CheckStateRole)

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
        if event.key() == Qt.Key_Down and event.modifiers() & Qt.AltModifier:
            self.showPopup()
            return

        ignored = {
            Qt.Key_Up,
            Qt.Key_Down,
            Qt.Key_PageDown,
            Qt.Key_PageUp,
            Qt.Key_Home,
            Qt.Key_End,
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
