"""Compact Fluent menu navigation with reusable RoundMenu popups."""

from PySide6.QtCore import QEvent, QKeyCombination, QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import QAbstractButton, QApplication, QHBoxLayout, QSizePolicy, QWidget
from shiboken6 import isValid

from ...common.config import isDarkTheme, qconfig
from ...common.font import getFont
from .menu import MenuAnimationType, RoundMenu


def _mnemonic(text):
    index = 0
    while index < len(text) - 1:
        if text[index] == '&':
            if text[index + 1] != '&':
                return text[index + 1].casefold()
            index += 1
        index += 1
    return ''


class _MenuBarButton(QAbstractButton):
    def __init__(self, action, bar):
        super().__init__(bar)
        self.action = action
        self.setFont(getFont(14))
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(lambda: bar._activateAction(action))
        action.changed.connect(self.sync)
        qconfig.themeChangedFinished.connect(self.update)
        self.sync()

    def sync(self):
        self.setText(self.action.text())
        self.setEnabled(self.action.isEnabled() and not self.action.isSeparator())
        self.setVisible(self.action.isVisible())
        self.setFixedSize(self.sizeHint())
        self.setAccessibleName(self.action.text().replace('&', ''))
        self.parentWidget()._actionChanged(self.action)
        self.update()

    def sizeHint(self):
        if self.action.isSeparator():
            return QSize(9, 32)
        width = self.fontMetrics().size(Qt.TextShowMnemonic, self.text()).width()
        return QSize(width + 16, 32)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def event(self, event):
        if event.type() == QEvent.Shortcut and not event.isAmbiguous():
            self.parentWidget()._activateAction(self.action, keyboard=True)
            return True
        return super().event(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        dark = isDarkTheme()
        shade = 255 if dark else 0
        if self.action.isSeparator():
            painter.setPen(QColor(shade, shade, shade, 30))
            painter.drawLine(4, 8, 4, 24)
            return
        bar = self.parentWidget()
        selected = (bar.activeMenu() is self.action.menu()
                    and bar.activeMenu() is not None)
        selected |= bar.hasFocus() and bar._keyboardAction is self.action
        if self.isEnabled() and (self.underMouse() or self.isDown() or selected):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(shade, shade, shade, 18 if self.isDown() else 9))
            painter.drawRoundedRect(QRectF(self.rect()), 5, 5)
        painter.setFont(self.font())
        painter.setPen(QColor('white' if dark else 'black'))
        if not self.isEnabled():
            painter.setOpacity(.4)
        mnemonic = Qt.TextShowMnemonic if bar.hasFocus() else Qt.TextHideMnemonic
        painter.drawText(self.rect(), Qt.AlignCenter | mnemonic, self.text())


class MenuBar(QWidget):
    """Top-level menu navigation; addMenu(str | RoundMenu) returns a RoundMenu.

    Native QWidget action APIs also support direct command actions and separators.
    Leaf QAction shortcuts are registered on a visible, zero-size child widget
    while their menu belongs to this bar; removing a menu removes that registration.
    Menus remain reusable and are not deleted by removeMenu()/clear().
    """

    triggered = Signal(QAction)
    activeMenuChanged = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = {}
        self._activeMenu = None
        self._keyboardAction = None
        self._previousFocus = None
        self._watchedMenus = set()
        self._leafActions = set()
        self._shortcutActions = set()
        self._filterInstalled = False
        self._popupState = [None]
        state = self._popupState
        self.destroyed.connect(lambda *_: MenuBar._closeTree(state[0]) if state[0] is not None else None)
        self._row = QHBoxLayout(self)
        self._row.setContentsMargins(0, 0, 0, 0)
        self._row.setSpacing(0)
        self._row.addStretch()
        self.setFixedHeight(32)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._shortcutHost = QWidget(self)
        self._shortcutHost.setFixedSize(0, 0)
        self._shortcutHost.setFocusPolicy(Qt.NoFocus)
        self._shortcutHost.show()
        self._focusShortcut = QShortcut(QKeySequence('F10'), self)
        self._focusShortcut.activated.connect(self._focusBar)

    def addMenu(self, menu):
        return self.insertMenu(None, menu)

    def insertMenu(self, before, menu):
        if isinstance(menu, str):
            menu = RoundMenu(menu, self)
        if not isinstance(menu, RoundMenu) or menu.isSubMenu:
            raise TypeError('MenuBar requires a top-level RoundMenu or a title string')
        if isinstance(before, RoundMenu):
            before = before.menuAction()
        if before is not None and before not in self.actions():
            raise ValueError('The insertion anchor is not in this MenuBar')
        self.insertAction(before, menu.menuAction())
        self._syncShortcuts()
        return menu

    def menus(self):
        return [action.menu() for action in self.actions() if isinstance(action.menu(), RoundMenu)]

    def removeMenu(self, menu):
        self.removeAction(menu.menuAction())

    def clear(self):
        self.closeActiveMenu()
        for action in self.actions():
            self.removeAction(action)

    def activeMenu(self):
        return self._activeMenu

    def setActiveMenu(self, menu):
        if menu is None:
            self.closeActiveMenu()
        elif menu not in self.menus():
            raise ValueError('The menu is not in this MenuBar')
        else:
            self._openMenu(menu, keyboard=True)

    def actionEvent(self, event):
        super().actionEvent(event)
        action = event.action()
        if event.type() == QEvent.ActionAdded:
            button = _MenuBarButton(action, self)
            self._buttons[action] = button
            self._row.insertWidget(self.actions().index(action), button)
        elif event.type() == QEvent.ActionRemoved:
            button = self._buttons.pop(action, None)
            if button is not None:
                if self._activeMenu is action.menu():
                    self.closeActiveMenu()
                self._row.removeWidget(button)
                button.hide()
                button.deleteLater()
        self._syncShortcuts()
        self.updateGeometry()

    def _actionChanged(self, action):
        if self._activeMenu is action.menu() and self._activeMenu is not None:
            if not action.isEnabled() or not action.isVisible():
                self.closeActiveMenu()
        self._syncShortcuts()

    def _syncShortcuts(self, *args):
        menus, actions, shortcuts = set(), set(), set()

        def visit(menu, enabled):
            if menu in menus or not isValid(menu):
                return
            menus.add(menu)
            actions.update(menu.menuActions())
            enabled = enabled and menu.menuAction().isEnabled() and menu.menuAction().isVisible()
            if enabled:
                shortcuts.update(menu.menuActions())
            for child in menu._subMenus:
                visit(child, enabled)

        for action in self.actions():
            if isinstance(action.menu(), RoundMenu):
                visit(action.menu(), action.isEnabled() and action.isVisible())
            elif not action.isSeparator():
                actions.add(action)
                if action.isEnabled() and action.isVisible():
                    shortcuts.add(action)
        for menu in menus - self._watchedMenus:
            menu.installEventFilter(self)
            menu.menuAction().changed.connect(self._syncShortcuts)
            model = menu.view.model()
            model.rowsInserted.connect(self._syncShortcuts)
            model.rowsRemoved.connect(self._syncShortcuts)
            model.modelReset.connect(self._syncShortcuts)
        for menu in self._watchedMenus - menus:
            if isValid(menu):
                menu.removeEventFilter(self)
                menu.menuAction().changed.disconnect(self._syncShortcuts)
                model = menu.view.model()
                model.rowsInserted.disconnect(self._syncShortcuts)
                model.rowsRemoved.disconnect(self._syncShortcuts)
                model.modelReset.disconnect(self._syncShortcuts)
        for action in actions - self._leafActions:
            action.triggered.connect(self._onTriggered)
        for action in self._leafActions - actions:
            if isValid(action):
                action.triggered.disconnect(self._onTriggered)
        for action in shortcuts - self._shortcutActions:
            self._shortcutHost.addAction(action)
        for action in self._shortcutActions - shortcuts:
            if isValid(action):
                self._shortcutHost.removeAction(action)
        self._shortcutActions = shortcuts
        self._watchedMenus, self._leafActions = menus, actions

    def _onTriggered(self):
        action = self.sender()
        self.closeActiveMenu()
        self.triggered.emit(action)

    def _activateAction(self, action, keyboard=False):
        if not action.isEnabled() or not action.isVisible() or action.isSeparator():
            return
        menu = action.menu()
        if isinstance(menu, RoundMenu):
            if menu is self._activeMenu:
                self.closeActiveMenu()
            else:
                self._openMenu(menu, keyboard)
        else:
            self.closeActiveMenu()
            action.trigger()

    def _openMenu(self, menu, keyboard=False):
        action = menu.menuAction()
        if not self.isEnabled() or not self.isVisible() or not action.isEnabled() or not action.isVisible():
            return
        if self._activeMenu is menu:
            return
        previous = self._previousFocus if self._activeMenu else QApplication.focusWidget()
        self.closeActiveMenu(restoreFocus=False)
        self._previousFocus = previous
        self._activeMenu = menu
        self._popupState[0] = menu
        self._keyboardAction = action
        QApplication.instance().installEventFilter(self)
        self._filterInstalled = True
        self._syncShortcuts()
        button = self._buttons[action]
        anchor = button.mapToGlobal(QPoint(12, button.height() + 3))
        menu.view.adjustSize()
        menu.adjustSize()
        menu.clearMask()
        menu.exec(anchor, aniType=MenuAnimationType.NONE)
        # Use the header's screen, including when keyboard activation leaves the
        # cursor on another monitor. RoundMenu's default manager uses the cursor.
        screen = button.screen().availableGeometry()
        margins = menu.layout().contentsMargins()
        x = min(max(anchor.x() - margins.left(), screen.left()), max(screen.left(), screen.right() - menu.width() + 1))
        y = anchor.y() - 4
        if y + menu.height() > screen.bottom() + 1:
            y = button.mapToGlobal(QPoint()).y() - menu.height() + margins.bottom() - 7
        y = min(max(y, screen.top()), max(screen.top(), screen.bottom() - menu.height() + 1))
        menu.move(x, y)
        menu.view.setFocus(Qt.PopupFocusReason)
        menu.view.setCurrentRow(-1)
        if keyboard:
            self._stepRow(menu, 1)
        self._updateButtons()
        self.activeMenuChanged.emit(menu)

    @staticmethod
    def _closeTree(menu):
        if not isValid(menu):
            return
        for child in menu._subMenus:
            MenuBar._closeTree(child)
        menu.timer.stop()
        if menu.aniManager is not None:
            menu.aniManager.ani.stop()
        menu.isHideBySystem = False
        menu.close()

    def closeActiveMenu(self, restoreFocus=True):
        menu = self._activeMenu
        self._activeMenu = None
        self._popupState[0] = None
        if self._filterInstalled:
            QApplication.instance().removeEventFilter(self)
            self._filterInstalled = False
        if menu is not None:
            self._closeTree(menu)
            self._keyboardAction = None
            self.activeMenuChanged.emit(None)
        self._updateButtons()
        previous = self._previousFocus
        self._previousFocus = None
        if restoreFocus and previous is not None and isValid(previous) and previous.isVisible() and previous.isEnabled():
            previous.setFocus(Qt.PopupFocusReason)

    def _updateButtons(self):
        for button in self._buttons.values():
            button.update()

    def _enabledActions(self):
        return [a for a in self.actions() if a.isEnabled() and a.isVisible() and not a.isSeparator()]

    def _focusBar(self):
        if not self.isEnabled() or not self.isVisible() or not self._enabledActions():
            return
        if self.hasFocus():
            self.closeActiveMenu()
            self.clearFocus()
        else:
            self._previousFocus = QApplication.focusWidget()
            self._keyboardAction = self._enabledActions()[0]
            self.setFocus(Qt.ShortcutFocusReason)
        self._updateButtons()

    def _moveHeader(self, step, openMenu=False):
        actions = self._enabledActions()
        if not actions:
            return
        current = self._keyboardAction
        index = actions.index(current) if current in actions else -1
        self._keyboardAction = actions[(index + step) % len(actions)]
        if openMenu:
            menu = self._keyboardAction.menu()
            if isinstance(menu, RoundMenu):
                self._openMenu(menu, keyboard=True)
            else:
                action = self._keyboardAction
                self.closeActiveMenu(restoreFocus=False)
                self._keyboardAction = action
                self.setFocus(Qt.PopupFocusReason)
        self._updateButtons()

    def _stepRow(self, menu, step):
        view = menu.view
        count = view.count()
        row = view.currentRow()
        if row < 0 and step < 0:
            row = count
        for _ in range(count):
            row = (row + step) % count
            item = view.item(row)
            if item.flags() & Qt.ItemIsEnabled and item.flags() & Qt.ItemIsSelectable:
                view.setCurrentRow(row)
                return

    def _currentPopup(self, obj):
        for menu in self._watchedMenus:
            if isValid(menu) and menu.isVisible() and (obj is menu or isinstance(obj, QWidget) and menu.isAncestorOf(obj)):
                return menu
        popup = QApplication.activePopupWidget()
        return popup if isinstance(popup, RoundMenu) and popup in self._watchedMenus else self._activeMenu

    def _openSubMenu(self, menu, item):
        child = item.data(Qt.UserRole)
        if not isinstance(child, RoundMenu):
            return False
        menu.timer.stop()
        menu._showSubMenu(item)
        menu.timer.stop()
        menu._onShowMenuTimeOut()
        child.view.setFocus(Qt.PopupFocusReason)
        child.view.setCurrentRow(-1)
        self._stepRow(child, 1)
        return True

    def _handleKey(self, event, menu=None):
        key = event.key()
        if menu is not None:
            if key == Qt.Key_F10:
                self.closeActiveMenu()
                return True
            if key == Qt.Key_Escape:
                if menu is not self._activeMenu:
                    menu.isHideBySystem = False
                    menu.close()
                    menu.parentMenu.view.setFocus(Qt.PopupFocusReason)
                else:
                    self.closeActiveMenu()
                return True
            if key == Qt.Key_Left and menu is not self._activeMenu:
                menu.isHideBySystem = False
                menu.close()
                menu.parentMenu.view.setFocus(Qt.PopupFocusReason)
                return True
            if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_Right):
                item = menu.view.currentItem()
                if item is not None and self._openSubMenu(menu, item):
                    return True
                if key != Qt.Key_Right:
                    if item is not None:
                        menu._onItemClicked(item)
                    return True
            if key in (Qt.Key_Down, Qt.Key_Up):
                self._stepRow(menu, 1 if key == Qt.Key_Down else -1)
                return True
            if key in (Qt.Key_Home, Qt.Key_End):
                menu.view.setCurrentRow(-1)
                self._stepRow(menu, 1 if key == Qt.Key_Home else -1)
                return True
            if event.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier):
                chord = QKeySequence(QKeyCombination(event.modifiers(), Qt.Key(key)))
                for action in self._shortcutActions:
                    if action.isEnabled() and action.isVisible() and any(chord == s for s in action.shortcuts()):
                        self.closeActiveMenu()
                        action.trigger()
                        return True
        if key in (Qt.Key_Left, Qt.Key_Right):
            self._moveHeader(-1 if key == Qt.Key_Left else 1, menu is not None)
            return True
        if event.modifiers() & Qt.AltModifier:
            for action in self._enabledActions():
                if _mnemonic(action.text()) and _mnemonic(action.text()) == event.text().casefold():
                    self._activateAction(action, keyboard=True)
                    return True
        if menu is None:
            if key in (Qt.Key_Down, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                action = self._keyboardAction
                if action is not None and isinstance(action.menu(), RoundMenu):
                    self._openMenu(action.menu(), keyboard=True)
                elif action is not None:
                    self._activateAction(action)
                return True
            if key == Qt.Key_Escape:
                self._keyboardAction = None
                self.clearFocus()
                self._updateButtons()
                return True
        return False

    def keyPressEvent(self, event):
        if self._handleKey(event):
            event.accept()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        kind = event.type()
        if isinstance(obj, RoundMenu) and obj in self._watchedMenus:
            if kind in (QEvent.ActionAdded, QEvent.ActionRemoved):
                self._syncShortcuts()
            elif kind == QEvent.Hide and obj is self._activeMenu:
                self.closeActiveMenu()
        if self._filterInstalled:
            if kind in (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
                point = self.mapFromGlobal(event.globalPosition().toPoint())
                button = next((b for b in self._buttons.values() if b.isVisible() and b.geometry().contains(point)), None)
                if button is not None:
                    if kind == QEvent.MouseMove and button.isEnabled() and button.action.menu() is not self._activeMenu:
                        if isinstance(button.action.menu(), RoundMenu):
                            self._openMenu(button.action.menu())
                    elif kind == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                        self._activateAction(button.action)
                    if kind != QEvent.MouseMove or button.action.menu() is self._activeMenu:
                        event.accept()
                        return True
            if kind in (QEvent.KeyPress, QEvent.ShortcutOverride) and isinstance(obj, QWidget):
                menu = self._currentPopup(obj)
                if menu is not None:
                    if kind == QEvent.ShortcutOverride:
                        event.accept()
                        return True
                    if self._handleKey(event, menu):
                        event.accept()
                        return True
            if obj is self.window() and kind in (QEvent.Move, QEvent.Resize, QEvent.Hide, QEvent.Close):
                self.closeActiveMenu()
        return super().eventFilter(obj, event)

    def hideEvent(self, event):
        self.closeActiveMenu()
        super().hideEvent(event)

    def changeEvent(self, event):
        if not self.isEnabled():
            self.closeActiveMenu()
        super().changeEvent(event)
