"""Fluent window with an expanded sidebar and accent-filled selection."""

from PySide6.QtCore import QEvent, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter

from ..common.config import isDarkTheme, qconfig
from ..common.icon import FluentIcon, drawIcon
from ..common.style_sheet import themeColor
from ..components.navigation.navigation_interface import NavigationInterface
from ..components.navigation.navigation_panel import (
    NavigationDisplayMode,
    NavigationPanel,
)
from ..components.navigation.navigation_widget import (
    NavigationTreeItem,
    NavigationTreeWidget,
    NavigationWidget,
)
from ..components.widgets.line_edit import SearchLineEdit
from .fluent_window import FluentTitleBar, FluentWindow
from .page_search import _PageSearchPopup


class _FilledNavigationTreeItem(NavigationTreeItem):
    def paintEvent(self, event):
        selected = self._canDrawIndicator()
        if not selected:
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        if not self.isEnabled():
            painter.setOpacity(0.4)
        elif self.isPressed:
            painter.setOpacity(0.7)
        painter.setPen(Qt.NoPen)
        color = themeColor()
        if self.isEnter:
            color = color.lighter(105) if isDarkTheme() else color.lighter(108)
        painter.setBrush(color)
        painter.drawRoundedRect(QRectF(self.rect()), 4, 4)

        foreground = QColor(Qt.black if isDarkTheme() else Qt.white)
        margins = self._margins()
        drawIcon(
            self._icon,
            painter,
            QRectF(11.5 + margins.left() + self._iconXOffset(), 10, 16, 16),
            fill=foreground.name(),
        )
        if not self.isCompacted:
            left = (
                44 + margins.left() if not self.icon().isNull() else margins.left() + 16
            )
            painter.setPen(foreground)
            painter.setFont(self.font())
            text_rect = QRectF(
                left, 0, self.width() - left - margins.right() - 13, self.height()
            )
            painter.drawText(
                text_rect,
                Qt.AlignVCenter,
                self.fontMetrics().elidedText(
                    self.text(), Qt.ElideRight, int(text_rect.width())
                ),
            )
        painter.end()
        self._drawDropDownArrow()

    def _drawDropDownArrow(self):
        if not self._canDrawIndicator():
            return super()._drawDropDownArrow()
        if self.isCompacted or self.treeWidget().isLeaf():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(0.4)
        elif self.isPressed:
            painter.setOpacity(0.7)
        painter.translate(self.width() - 20, 18)
        painter.rotate(self.arrowAngle)
        FluentIcon.ARROW_DOWN.render(
            painter,
            QRectF(-5, -5, 9.6, 9.6),
            fill="#000000" if isDarkTheme() else "#ffffff",
        )


class _FilledNavigationTreeWidget(NavigationTreeWidget):
    def _createItemWidget(self, icon, text, isSelectable):
        return _FilledNavigationTreeItem(icon, text, isSelectable, self)


class _FilledNavigationPanel(NavigationPanel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIndicatorAnimationEnabled(False)
        self.vBoxLayout.setContentsMargins(12, 0, 12, 12)
        for layout in (self.topLayout, self.bottomLayout, self.scrollLayout):
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)
        self.setExpandWidth(216)

    def _createNavigationItem(self, icon, text, selectable):
        return _FilledNavigationTreeWidget(icon, text, selectable, self)

    def _registerWidget(self, routeKey, parentRouteKey, widget, onClick, tooltip):
        # NavigationPanel's default width setter changes a class-wide value.
        # Keep this window's narrower items local to this panel instead.
        for item in [widget] + widget.findChildren(NavigationWidget):
            item.EXPAND_WIDTH = self.expandWidth - 24
        super()._registerWidget(routeKey, parentRouteKey, widget, onClick, tooltip)

    def setExpandWidth(self, width):
        if width <= 48:
            return
        self.expandWidth = width
        for item in self.findChildren(NavigationWidget):
            item.EXPAND_WIDTH = width - 24
            if not item.isCompacted:
                item.setFixedWidth(item.EXPAND_WIDTH)
        if self.displayMode == NavigationDisplayMode.EXPAND:
            self.setFixedWidth(width)


class _FilledNavigationInterface(NavigationInterface):
    def __init__(self, parent=None):
        super().__init__(
            parent, showMenuButton=False, showReturnButton=False, collapsible=False
        )
        self.searchLineEdit = SearchLineEdit(self.panel)
        self.searchLineEdit.setPlaceholderText(self.tr("Search"))
        self.searchLineEdit.setFixedHeight(32)
        self.panel.topLayout.insertWidget(0, self.searchLineEdit)
        self.panel.topLayout.insertSpacing(1, 8)
        self.displayModeChanged.connect(self._updateSearchVisibility)
        qconfig.themeChanged.connect(self.panel.update)
        qconfig.themeColorChanged.connect(self.panel.update)

    def _createPanel(self):
        return _FilledNavigationPanel(self)

    def _updateSearchVisibility(self, mode):
        self.searchLineEdit.setVisible(
            mode in (NavigationDisplayMode.EXPAND, NavigationDisplayMode.MENU)
        )


class _FilledFluentTitleBar(FluentTitleBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.hBoxLayout.setContentsMargins(24, 0, 0, 0)


class FilledFluentWindow(FluentWindow):
    """Fluent window with a search box and accent-filled sidebar selection.

    Uses the same addSubInterface(), switchTo(), routing and Mica APIs as
    FluentWindow. The sidebar is expanded by default. Typing in searchLineEdit
    searches registered page names; selecting a result navigates to that page.
    """

    pageSearchActivated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitleBar(_FilledFluentTitleBar(self))
        self.hBoxLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.widgetLayout.setContentsMargins(0, 0, 0, 0)
        self.searchLineEdit = self.navigationInterface.searchLineEdit
        self._searchPopup = _PageSearchPopup(self.searchLineEdit, self)
        self._searchQuery = ""
        self.searchLineEdit.installEventFilter(self)
        self.searchLineEdit.textChanged.connect(self._updatePageSearch)
        self.searchLineEdit.searchSignal.connect(self._showPageSearch)
        self.searchLineEdit.clearSignal.connect(self._searchPopup.hide)
        self._searchPopup.activated.connect(self._activateSearchResult)
        qconfig.themeChangedFinished.connect(self._refreshPageSearch)
        self.titleBar.raise_()

    def _pageSearchResults(self, text):
        tokens = text.strip().casefold().split()
        if not tokens:
            return []
        pages = {
            self.stackedWidget.widget(i).objectName()
            for i in range(self.stackedWidget.count())
        }
        ranked = []
        query = " ".join(tokens)
        for key, entry in self.navigationInterface.panel.items.items():
            item = entry.widget
            if key not in pages or not item.isSelectable or not item.isEnabled():
                continue
            title = item.text()
            folded = title.casefold()
            if all(token in folded for token in tokens):
                score = 0 if folded == query else 1 if folded.startswith(query) else 2
                ranked.append((score, key, title, item.icon()))
        ranked.sort(key=lambda result: result[0])
        return [(key, title, icon) for _, key, title, icon in ranked]

    def _updatePageSearch(self, text):
        query = text.strip()
        if not query:
            self._searchQuery = ""
            self._searchPopup.hide()
            return
        self._searchPopup.setResults(
            self._pageSearchResults(query), query == self._searchQuery
        )
        self._searchQuery = query
        if self.searchLineEdit.hasFocus() or self._searchPopup.isVisible():
            self._searchPopup.show()

    def _showPageSearch(self, text):
        self.searchLineEdit.setFocus()
        self._updatePageSearch(text)

    def _refreshPageSearch(self):
        if self._searchPopup.isVisible():
            self._updatePageSearch(self.searchLineEdit.text())

    def _activateSearchResult(self, key):
        entry = self.navigationInterface.panel.items.get(key)
        if not entry or not entry.widget.isEnabled():
            return self._refreshPageSearch()
        for i in range(self.stackedWidget.count()):
            page = self.stackedWidget.widget(i)
            if page.objectName() == key:
                self._searchPopup.hide()
                self.switchTo(page)
                page.setFocus(Qt.OtherFocusReason)
                self.pageSearchActivated.emit(page)
                return

    def addSubInterface(self, *args, **kwargs):
        item = super().addSubInterface(*args, **kwargs)
        if hasattr(self, "_searchPopup"):
            self._refreshPageSearch()
        return item

    def removeInterface(self, interface, isDelete=False):
        super().removeInterface(interface, isDelete)
        self._refreshPageSearch()

    def eventFilter(self, obj, event):
        if obj is getattr(self, "searchLineEdit", None):
            if event.type() == QEvent.FocusIn and self.searchLineEdit.text().strip():
                self._updatePageSearch(self.searchLineEdit.text())
            elif event.type() == QEvent.KeyPress:
                key = event.key()
                if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Return, Qt.Key_Enter):
                    if self.searchLineEdit.text().strip():
                        if not self._searchPopup.isVisible():
                            self._showPageSearch(self.searchLineEdit.text())
                        if key in (Qt.Key_Return, Qt.Key_Enter):
                            self._searchPopup.activateCurrent()
                        else:
                            self._searchPopup.moveSelection(
                                1 if key == Qt.Key_Down else -1
                            )
                        return True
                elif key == Qt.Key_Escape and self._searchPopup.isVisible():
                    self._searchPopup.hide()
                    return True
                elif key in (Qt.Key_Tab, Qt.Key_Backtab):
                    self._searchPopup.hide()
        return super().eventFilter(obj, event)

    def _createNavigationInterface(self):
        return _FilledNavigationInterface(self)

    def resizeEvent(self, event):
        self.titleBar.move(0, 0)
        self.titleBar.resize(self.width(), self.titleBar.height())
