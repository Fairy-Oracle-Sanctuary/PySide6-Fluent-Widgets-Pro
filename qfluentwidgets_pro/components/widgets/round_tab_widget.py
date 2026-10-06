"""QTabWidget-style page container using the existing RoundTabBar."""

from contextlib import contextmanager

from PySide6.QtCore import QEvent, QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QPen, QShortcut, QTransform
from PySide6.QtWidgets import QStackedWidget

from ...common.config import qconfig
from ...common.style_sheet import isDarkTheme
from .round_tab_bar import RoundTabBar, RoundTabItem
from .tab_view import TabWidget


class _WidgetTabItem(RoundTabItem):
    def _drawSelectedBackground(self, painter):
        # The container paints a single tab + page silhouette behind this item.
        pass


class _WidgetTabBar(RoundTabBar):
    def _createTabItem(self, text, icon):
        return _WidgetTabItem(text, self.view, icon)

    def __call__(self):
        # TabWidget uses an attribute; QTabWidget callers use tabBar().
        return self


class _RoundTabStack(QStackedWidget):
    def paintEvent(self, event):
        # Keep pages transparent; the owner supplies the unified fill and frame.
        pass


class RoundTabWidget(TabWidget):
    """Top-rounded tabs with application-provided QWidget pages.

    Supports addTab(page, label) and addTab(page, icon, label), plus the existing
    Fluent addTab(page, label, icon, routeKey) form. Closing emits a request;
    removeTab()/clear() keep pages alive, just like QTabWidget.
    """

    def __init__(self, parent=None):
        self._pageChangeDepth = 0
        self._autoHide = False
        super().__init__(parent)
        self.vBoxLayout.setSpacing(0)
        self.stackedWidget.currentChanged.connect(self._onStackChanged)
        qconfig.themeChangedFinished.connect(self.update)
        qconfig.themeChangedFinished.connect(self.stackedWidget.update)
        self.tabBar.horizontalScrollBar().valueChanged.connect(self.stackedWidget.update)
        self.tabBar.horizontalScrollBar().valueChanged.connect(self.update)
        self._tabShortcuts = []
        for sequence, step in (('Ctrl+Tab', 1), ('Ctrl+Shift+Tab', -1)):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.WidgetWithChildrenShortcut)
            shortcut.activated.connect(lambda step=step: self._cycleTab(step))
            self._tabShortcuts.append(shortcut)

    def _createTabBar(self):
        return _WidgetTabBar(self)

    def _createStackedWidget(self):
        return _RoundTabStack(self)

    def _framePath(self, outline=False):
        edge = .5 if outline else 0
        contentRect = QRectF(self.stackedWidget.geometry()).adjusted(edge, edge, -edge, -edge)
        path = QPainterPath()
        path.addRoundedRect(contentRect, 8, 8)
        item = self.tabBar.currentTab()
        if item is None or item.isHidden() or self.tabBar.isHidden():
            return path
        position = item.mapTo(self, QPoint())
        # Share the exact baseline with the page outline, including its half-pixel
        # pen inset, so there cannot be two independently antialiased endpoints.
        # An imperceptible overlap makes QPainterPath merge the common edge,
        # rather than retain two touching contours and stroke their shared seam.
        baseline = contentRect.top() + .001
        tabPath = item._selectedPath(outline, bottom=baseline - position.y())
        tabPath.closeSubpath()
        tabPath = QTransform.fromTranslate(position.x(), position.y()).map(tabPath)
        clip = QPainterPath()
        viewport = self.tabBar.viewport()
        viewportRect = QRectF(viewport.rect())
        viewportRect.moveTopLeft(viewport.mapTo(self, QPoint()))
        viewportRect.setBottom(baseline)
        clip.addRect(viewportRect)
        return path.united(tabPath.intersected(clip))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = (self.tabBar.darkSelectedBackgroundColor if isDarkTheme()
                 else self.tabBar.lightSelectedBackgroundColor)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawPath(self._framePath())
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 18) if isDarkTheme() else QColor(0, 0, 0, 15), 1))
        painter.drawPath(self._framePath(outline=True))

    def _connectTabBarSignalToSlot(self):
        self.tabBar.tabCloseRequested.connect(self.tabCloseRequested)
        self.tabBar.tabBarClicked.connect(self.tabBarClicked)
        self.tabBar.tabBarDoubleClicked.connect(self.tabBarDoubleClicked)
        self.tabBar.tabAddRequested.connect(self.tabAddRequested)
        self.tabBar.currentChanged.connect(self._onCurrentTabChanged)
        self.tabBar.tabMoved.connect(self._onTabMoved)

    @contextmanager
    def _pageChange(self, notifyIndex=True):
        index, page = self.currentIndex(), self.currentWidget()
        self._pageChangeDepth += 1
        try:
            yield
        finally:
            self._pageChangeDepth -= 1
            if not self._pageChangeDepth:
                self._syncBar()
                self._updateAutoHide()
                self.stackedWidget.update()
                self.update()
                if (notifyIndex and index != self.currentIndex()) or page is not self.currentWidget():
                    self.currentChanged.emit(self.currentIndex())

    def _syncBar(self):
        index = self.currentIndex()
        if 0 <= index < self.tabBar.count():
            self.tabBar.setCurrentIndex(index)

    def _onStackChanged(self, index):
        if not self._pageChangeDepth:
            self._syncBar()
            self.stackedWidget.update()
            self.update()
            self.currentChanged.emit(index)

    def _onCurrentTabChanged(self, index):
        if not self._pageChangeDepth:
            self.setCurrentIndex(index)

    def _onTabMoved(self, fromIndex, toIndex):
        with self._pageChange():
            super()._onTabMoved(fromIndex, toIndex)

    def addTab(self, widget, label, icon=None, routeKey=None):
        return self.insertTab(-1, widget, label, icon, routeKey)

    def insertTab(self, index, widget, label, icon=None, routeKey=None):
        if not isinstance(label, str) and isinstance(icon, str):
            label, icon = icon, label
        if not isinstance(label, str):
            raise TypeError('The tab label must be a string')
        if widget is None or self.indexOf(widget) >= 0:
            return -1
        if routeKey is not None and self.tabBar.tab(routeKey) is not None:
            raise ValueError(f'The route key `{routeKey}` is duplicated.')
        index = index if 0 <= index <= self.count() else self.count()
        with self._pageChange(notifyIndex=False):
            result = super().insertTab(index, widget, label, icon, routeKey)
            self.tabBar.tabItem(result).installEventFilter(self)
        return result

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Move, QEvent.Resize, QEvent.Show, QEvent.Hide):
            # Keep the frame opening attached to animated or resized tabs.
            self.stackedWidget.update()
            self.update()
        return super().eventFilter(watched, event)

    def indexOf(self, widget):
        return self.stackedWidget.indexOf(widget) if widget is not None else -1

    def setCurrentIndex(self, index):
        if not 0 <= index < self.count():
            return
        with self._pageChange():
            super().setCurrentIndex(index)

    def removeTab(self, index):
        if not 0 <= index < self.count():
            return
        with self._pageChange():
            page = self.widget(index)
            target = self.currentWidget()
            if target is page:
                candidates = list(range(index + 1, self.count())) + list(range(index - 1, -1, -1))
                available = [i for i in candidates if self.isTabVisible(i) and self.isTabEnabled(i)]
                target = self.widget((available or candidates)[0]) if candidates else None
            super().removeTab(index)
            page.hide()
            if target is not None:
                self.stackedWidget.setCurrentWidget(target)

    def clear(self):
        # Qt clears from the last tab and reports each resulting page change.
        while self.count():
            self.removeTab(self.count() - 1)

    def setTabVisible(self, index, visible):
        item = self.tabBar.tabItem(index)
        if item is None or visible == (not item.isHidden()):
            return
        with self._pageChange():
            item.setVisible(visible)
            if not visible and index == self.currentIndex():
                self._selectAvailable(index, allowDisabled=True)
            elif visible and not self.isTabVisible(self.currentIndex()):
                self.setCurrentIndex(index)
            self.stackedWidget.update()

    def setTabEnabled(self, index, enabled):
        if not 0 <= index < self.count():
            return
        with self._pageChange():
            super().setTabEnabled(index, enabled)
            self.widget(index).setEnabled(enabled)
            if not enabled and index == self.currentIndex():
                self._selectAvailable(index)

    def _selectAvailable(self, index, allowDisabled=False):
        candidates = list(range(index + 1, self.count())) + list(range(index - 1, -1, -1))
        for candidate in candidates:
            if self.isTabVisible(candidate) and self.isTabEnabled(candidate):
                self.setCurrentIndex(candidate)
                return
        if allowDisabled:
            for candidate in candidates:
                if self.isTabVisible(candidate):
                    self.setCurrentIndex(candidate)
                    return

    def _cycleTab(self, step):
        for offset in range(1, self.count() + 1):
            index = (self.currentIndex() + offset * step) % self.count()
            if self.isTabVisible(index) and self.isTabEnabled(index):
                self.setCurrentIndex(index)
                return

    def setTabSelectedBackgroundColor(self, light, dark):
        super().setTabSelectedBackgroundColor(light, dark)
        self.stackedWidget.update()
        self.update()

    def setTabBarAutoHide(self, enabled):
        self._autoHide = bool(enabled)
        self._updateAutoHide()

    def tabBarAutoHide(self):
        return self._autoHide

    def _updateAutoHide(self):
        self.tabBar.setVisible(not self._autoHide or self.count() >= 2)

    def setTabWhatsThis(self, index, text):
        item = self.tabBar.tabItem(index)
        if item is not None:
            item.setWhatsThis(text)

    def tabWhatsThis(self, index):
        item = self.tabBar.tabItem(index)
        return item.whatsThis() if item is not None else ''
