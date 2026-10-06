"""A page-agnostic Fluent setup window with an existing PipsPager."""

import sys
import weakref
from ctypes import byref, c_int

from PySide6.QtCore import QEvent, QSignalBlocker, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import QApplication, QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget
from shiboken6 import isValid

from ..common.config import isDarkTheme, qconfig
from ..components.widgets.button import HyperlinkButton, PrimaryPushButton
from ..components.widgets.pips_pager import PipsPager
from ..common.style_sheet import FluentStyleSheet
from ..qframelesswindow import FramelessWindow


class _GuideFooter(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(80)
        qconfig.themeChangedFinished.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 24) if isDarkTheme() else QColor(0, 120, 100, 9))


class GuideWindow(FramelessWindow):
    """Independent, modeless wizard. Pages and business logic belong to the caller.

    Override validatePage(page) to prevent forward navigation/finish. setCurrentIndex
    is unconditional; user navigation (including forward pip clicks) is validated.
    Removing a page hides and detaches it without deleting it. The window does not
    save settings, perform network requests or clear page contents when closed.
    parent is only a centering/lifetime reference, not a native window owner:
    show() creates a regular taskbar-eligible window even when parent is supplied.
    """

    currentIndexChanged = Signal(int)
    finished = Signal()
    cancelled = Signal()

    def __init__(self, parent=None):
        # An owned native window is normally omitted from the Windows taskbar.
        # Keep the native parent unset, including when a centering parent is given.
        super().__init__(None)
        self._guideParent = weakref.ref(parent) if parent is not None else None
        if parent is not None:
            parent.destroyed.connect(self.close)
        self._isMicaEnabled = False
        self._lightBackgroundColor = QColor('#f7f9fc')
        self._darkBackgroundColor = QColor('#272727')
        self.setStyleSheet('GuideWindow { background-color: transparent; }')
        self.setAutoFillBackground(False)
        FluentStyleSheet.FLUENT_WINDOW.apply(self.titleBar)
        self.titleBar.minBtn.hide()
        self.titleBar.maxBtn.hide()
        self.titleBar.setDoubleClickEnabled(False)
        qconfig.themeChangedFinished.connect(self._updateWindowEffect)
        self._nextEnabled = True
        self._sessionEnded = False
        self._centered = False
        self._lastPage = None
        self._lastIndex = -1
        self.stackedWidget = QStackedWidget(self)
        self.footer = _GuideFooter(self)
        self.pipsPager = PipsPager(Qt.Horizontal, self.footer)
        self.previousButton = HyperlinkButton(self.footer)
        self.previousButton.setText(self.tr('Previous'))
        self.nextButton = PrimaryPushButton(self.tr('Next'), self.footer)
        for button in (self.previousButton, self.nextButton):
            button.setFixedSize(120, 32)
        self.footerLayout = QHBoxLayout(self.footer)
        self.footerLayout.setContentsMargins(28, 0, 28, 0)
        self.footerLayout.setSpacing(12)
        self.footerLayout.addWidget(self.pipsPager)
        self.footerLayout.addStretch()
        self.footerLayout.addWidget(self.previousButton)
        self.footerLayout.addWidget(self.nextButton)
        self.contentLayout = QVBoxLayout(self)
        self.contentLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.contentLayout.setSpacing(0)
        self.contentLayout.addWidget(self.stackedWidget, 1)
        self.contentLayout.addWidget(self.footer)
        self.previousButton.clicked.connect(self.previous)
        self.nextButton.clicked.connect(self.next)
        # QListWidget's row signal also covers keyboard selection. The pager's
        # custom signal is emitted before it actually changes its current item.
        self.pipsPager.currentRowChanged.connect(self._onPipChanged)
        self.stackedWidget.currentChanged.connect(self._syncNavigation)
        self.stackedWidget.widgetRemoved.connect(self._syncNavigation)
        self._escapeShortcut = QShortcut(QKeySequence('Esc'), self)
        self._escapeShortcut.activated.connect(self.cancel)
        self.setMinimumSize(440, 300)
        self.resize(670, 460)
        self._syncNavigation()
        self.titleBar.raise_()
        self.setMicaEffectEnabled(True)

    def setMicaEffectEnabled(self, enabled):
        """Enable native Mica on Windows 11; use a solid themed fallback elsewhere."""
        supported = (sys.platform == 'win32' and sys.getwindowsversion().build >= 22000)
        self._isMicaEnabled = bool(enabled and supported)
        self._updateWindowEffect()

    def isMicaEffectEnabled(self):
        return self._isMicaEnabled

    def setCustomBackgroundColor(self, light, dark):
        """Customize the solid fallback used when Mica is off/unavailable."""
        self._lightBackgroundColor, self._darkBackgroundColor = QColor(light), QColor(dark)
        self.update()

    def _updateWindowEffect(self):
        if sys.platform == 'win32' and QApplication.platformName() == 'windows':
            import win32con
            import win32gui
            hwnd = int(self.winId())
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            desired = (style | win32con.WS_EX_APPWINDOW) & ~win32con.WS_EX_TOOLWINDOW
            if desired != style:
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, desired)
        if sys.platform == 'win32' and sys.getwindowsversion().build >= 22000:
            if self._isMicaEnabled:
                self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())
            else:
                self.windowEffect.removeBackgroundEffect(self.winId())
                # The bundled helper clears the accent policy, but not the DWM
                # system backdrop attribute set by setMicaEffect(). Clear both.
                attribute = 38 if sys.getwindowsversion().build >= 22523 else 1029
                value = c_int(1 if attribute == 38 else 0)
                self.windowEffect.DwmSetWindowAttribute(int(self.winId()), attribute, byref(value), 4)
                self.windowEffect.DwmSetWindowAttribute(int(self.winId()), 20, byref(c_int(int(isDarkTheme()))), 4)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._isMicaEnabled:
            # Clear, rather than cover, the native DWM backdrop. Do not use
            # WA_TranslucentBackground/WS_EX_LAYERED for a Mica window.
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(self.rect(), Qt.transparent)
        else:
            painter.fillRect(self.rect(), self._darkBackgroundColor if isDarkTheme() else self._lightBackgroundColor)

    def addPage(self, page):
        return self.insertPage(self.count(), page)

    def insertPage(self, index, page):
        if not isinstance(page, QWidget):
            raise TypeError('GuideWindow pages must be QWidget instances')
        if page is self or page.isAncestorOf(self):
            raise ValueError('A window or one of its ancestors cannot be a guide page')
        if self.stackedWidget.indexOf(page) >= 0:
            raise ValueError('This page is already in the GuideWindow')
        if not 0 <= index <= self.count():
            raise IndexError('Page insertion index is out of range')
        result = self.stackedWidget.insertWidget(index, page)
        self._syncNavigation()
        return result

    def removePage(self, page):
        if self.stackedWidget.indexOf(page) < 0:
            return
        self.stackedWidget.removeWidget(page)
        page.hide()
        page.setParent(None)
        self._syncNavigation()

    def count(self):
        return self.stackedWidget.count()

    def page(self, index):
        return self.stackedWidget.widget(index)

    def currentIndex(self):
        return self.stackedWidget.currentIndex()

    def currentPage(self):
        return self.stackedWidget.currentWidget()

    def setCurrentIndex(self, index):
        if not 0 <= index < self.count():
            raise IndexError('Page index is out of range')
        self.stackedWidget.setCurrentIndex(index)

    def setNextEnabled(self, enabled):
        self._nextEnabled = bool(enabled)
        self._syncNavigation()

    def setStepNavigationEnabled(self, enabled):
        """Disable clickable pips when the application requires sequential steps."""
        self.pipsPager.setEnabled(enabled)

    def validatePage(self, page):
        """Return False to keep the current page when moving forward or finishing."""
        return True

    def _requestIndex(self, index):
        if not 0 <= index < self.count() or index == self.currentIndex():
            return False
        if index > self.currentIndex() and (not self._nextEnabled or not self.validatePage(self.currentPage())):
            return False
        self.setCurrentIndex(index)
        return True

    def previous(self):
        return self._requestIndex(self.currentIndex() - 1)

    def next(self):
        if not self.count() or not self._nextEnabled:
            return False
        if self.currentIndex() == self.count() - 1:
            return self.finish()
        return self._requestIndex(self.currentIndex() + 1)

    def finish(self):
        if self._sessionEnded or not self.count() or self.currentIndex() != self.count() - 1:
            return False
        if not self._nextEnabled or not self.validatePage(self.currentPage()):
            return False
        self._sessionEnded = True
        self.finished.emit()
        self.close()
        return True

    def cancel(self):
        self.close()

    def _onPipChanged(self, index):
        self._requestIndex(index)
        # PipsPager emits before it updates its own current item. Schedule the
        # correction after its click handler if validation refused the change.
        QTimer.singleShot(0, self, self._syncNavigation)

    def _syncNavigation(self, *args):
        index, count = self.currentIndex(), self.count()
        with QSignalBlocker(self.pipsPager):
            if self.pipsPager.getPageNumber() != count:
                self.pipsPager.setPageNumber(count)
            if index >= 0:
                self.pipsPager.setCurrentIndex(index)
        self.pipsPager.setVisible(count > 1)
        self.previousButton.setVisible(index > 0)
        self.previousButton.setEnabled(index > 0)
        self.nextButton.setEnabled(count > 0 and self._nextEnabled)
        self.nextButton.setText(self.tr('Finish') if count and index == count - 1 else self.tr('Next'))
        page = self.currentPage()
        if index != self._lastIndex or page is not self._lastPage:
            self._lastIndex, self._lastPage = index, page
            self.currentIndexChanged.emit(index)

    def moveToCenter(self):
        owner = self._guideParent() if self._guideParent is not None else None
        if owner is not None and not isValid(owner):
            owner = None
        ownerVisible = owner is not None and owner.isVisible()
        screen = (owner.window().screen() if ownerVisible else self.screen()).availableGeometry()
        bounds = owner.window().frameGeometry() if ownerVisible else screen
        point = bounds.center() - self.rect().center()
        self.move(max(screen.left(), min(point.x(), screen.right() - self.width() + 1)),
                  max(screen.top(), min(point.y(), screen.bottom() - self.height() + 1)))
        self._centered = True

    def showEvent(self, event):
        self._sessionEnded = False
        if not self._centered:
            self.moveToCenter()
        super().showEvent(event)
        self._updateWindowEffect()

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted() and not self._sessionEnded:
            self._sessionEnded = True
            self.cancelled.emit()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange and hasattr(self, 'previousButton'):
            self.previousButton.setText(self.tr('Previous'))
            self._syncNavigation()
        super().changeEvent(event)
