# coding:utf-8
from enum import Enum
from typing import Union

from PySide6.QtCore import (
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QWidget

from ...common.animation import ScaleSlideAnimation
from ...common.color import autoFallbackThemeColor
from ...common.icon import FluentIcon as FIF
from ...common.icon import FluentIconBase
from ...common.router import qrouter
from ...common.style_sheet import FluentStyleSheet
from ..widgets.scroll_area import ScrollArea
from ..widgets.tool_tip import ToolTipFilter
from .navigation_widget import (
    NavigationPushButton,
    NavigationToolButton,
    NavigationWidget,
)


class TopNavigationDisplayMode(Enum):
    """Top navigation display mode"""

    COMPACT = 0  # only icons
    EXPAND = 1  # icons + text


class TopNavigationItemPosition(Enum):
    """Top navigation item position"""

    LEFT = 0
    CENTER = 1
    RIGHT = 2


class TopNavigationPanel(QFrame):
    """Horizontal navigation panel at top"""

    displayModeChanged = Signal(TopNavigationDisplayMode)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._isReturnButtonVisible = False
        self._displayMode = TopNavigationDisplayMode.COMPACT

        # indicator animation (like Pivot)
        self.slideAni = ScaleSlideAnimation(self, Qt.Horizontal)
        self.lightIndicatorColor = QColor()
        self.darkIndicatorColor = QColor()

        self.scrollArea = ScrollArea(self)
        self.scrollWidget = QWidget()

        self.returnButton = NavigationToolButton(FIF.RETURN, self)

        self.hBoxLayout = QHBoxLayout(self)
        self.leftLayout = QHBoxLayout()
        self.centerLayout = QHBoxLayout()
        self.rightLayout = QHBoxLayout()
        self.scrollLayout = QHBoxLayout(self.scrollWidget)

        self.items = {}  # type: Dict[str, NavigationWidget]
        self.history = qrouter
        self._currentRouteKey = None

        self.expandWidth = 800
        self._isIndicatorAnimationEnabled = True

        self.__initWidget()

    def __initWidget(self):
        self.setFixedHeight(48)
        self.setAttribute(Qt.WA_StyledBackground)
        self.window().installEventFilter(self)

        self.returnButton.hide()
        self.returnButton.setDisabled(True)

        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.verticalScrollBar().setEnabled = False
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)

        self.history.emptyChanged.connect(self.returnButton.setDisabled)
        self.returnButton.clicked.connect(self.history.pop)
        self.slideAni.valueChanged.connect(lambda: self.update())
        self.slideAni.finished.connect(self._onIndicatorAniFinished)

        # add tool tip
        self.returnButton.installEventFilter(ToolTipFilter(self.returnButton, 1000))
        self.returnButton.setToolTip(self.tr("Back"))

        self.scrollWidget.setObjectName("scrollWidget")
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self)
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self.scrollWidget)
        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(12, 0, 12, 0)
        self.hBoxLayout.setSpacing(0)

        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.centerLayout.setContentsMargins(0, 0, 0, 0)
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)

        self.leftLayout.setSpacing(4)
        self.centerLayout.setSpacing(4)
        self.rightLayout.setSpacing(4)
        self.scrollLayout.setSpacing(4)

        self.hBoxLayout.addLayout(self.leftLayout)
        self.hBoxLayout.addWidget(self.scrollArea, 1)
        self.hBoxLayout.addLayout(self.rightLayout)

        self.leftLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.centerLayout.setAlignment(Qt.AlignCenter)
        self.rightLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.scrollLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.leftLayout.addWidget(self.returnButton)

    def displayMode(self):
        return self._displayMode

    def setDisplayMode(self, mode: TopNavigationDisplayMode):
        if self._displayMode == mode:
            return

        self._displayMode = mode
        self.displayModeChanged.emit(mode)

        for item in self.items.values():
            item.setCompacted(mode == TopNavigationDisplayMode.COMPACT)

    def isCompact(self):
        return self._displayMode == TopNavigationDisplayMode.COMPACT

    def expand(self, useAni=True):
        self.setDisplayMode(TopNavigationDisplayMode.EXPAND)

    def collapse(self, useAni=True):
        self.setDisplayMode(TopNavigationDisplayMode.COMPACT)

    def toggle(self):
        if self.isCompact():
            self.expand()
        else:
            self.collapse()

    def widget(self, routeKey: str):
        if routeKey not in self.items:
            raise ValueError(f"`{routeKey}` is illegal.")

        return self.items[routeKey]

    def addItem(
        self,
        routeKey: str,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        onClick=None,
        selectable=True,
        position=TopNavigationItemPosition.LEFT,
        tooltip: str = None,
        expanded: bool = False,
    ):
        """add navigation item

        Parameters
        ----------
        expanded: bool
            whether to show text for this specific item
        """
        return self.insertItem(
            -1, routeKey, icon, text, onClick, selectable, position, tooltip, expanded
        )

    def insertItem(
        self,
        index: int,
        routeKey: str,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        onClick=None,
        selectable=True,
        position=TopNavigationItemPosition.LEFT,
        tooltip: str = None,
        expanded: bool = False,
    ):
        """insert navigation item

        Parameters
        ----------
        expanded: bool
            whether to show text for this specific item
        """
        if routeKey in self.items:
            return self.items[routeKey]

        w = TopNavigationPushButton(icon, text, selectable, self)
        w.setCompacted(self.isCompact())
        if expanded:
            w.setExpanded(True)
        self.insertWidget(index, routeKey, w, onClick, position, tooltip)
        return w

    def setItemExpanded(self, routeKey: str, expanded: bool):
        """set whether a specific item shows its text

        Parameters
        ----------
        routeKey: str
            the route key of the item

        expanded: bool
            whether to show text for this item
        """
        if routeKey not in self.items:
            return

        widget = self.items[routeKey]
        if isinstance(widget, TopNavigationPushButton):
            widget.setExpanded(expanded)

    def addWidget(
        self,
        routeKey: str,
        widget: NavigationWidget,
        onClick=None,
        position=TopNavigationItemPosition.LEFT,
        tooltip: str = None,
    ):
        """add custom widget"""
        self.insertWidget(-1, routeKey, widget, onClick, position, tooltip)

    def insertWidget(
        self,
        index: int,
        routeKey: str,
        widget: NavigationWidget,
        onClick=None,
        position=TopNavigationItemPosition.LEFT,
        tooltip: str = None,
    ):
        """insert custom widget"""
        if routeKey in self.items:
            return

        self._registerWidget(routeKey, widget, onClick, tooltip)
        self._insertWidgetToLayout(index, widget, position)

    def _registerWidget(
        self, routeKey: str, widget: NavigationWidget, onClick, tooltip: str = None
    ):
        """register widget"""
        widget.clicked.connect(self._onWidgetClicked)

        if onClick is not None:
            widget.clicked.connect(onClick)

        widget.setProperty("routeKey", routeKey)
        self.items[routeKey] = widget

        if tooltip:
            widget.setToolTip(tooltip)
            widget.installEventFilter(ToolTipFilter(widget, 1000))

    def _insertWidgetToLayout(
        self, index: int, widget: NavigationWidget, position: TopNavigationItemPosition
    ):
        """insert widget to layout"""
        if position == TopNavigationItemPosition.LEFT:
            widget.setParent(self)
            # returnButton is at index 0, so items should be inserted after it
            # if index is -1 (append), insert at the end; otherwise insert at index+1
            insertIndex = index + 1 if index >= 0 else -1
            self.leftLayout.insertWidget(
                insertIndex, widget, 0, Qt.AlignLeft | Qt.AlignVCenter
            )
        elif position == TopNavigationItemPosition.CENTER:
            widget.setParent(self)
            self.centerLayout.insertWidget(index, widget, 0, Qt.AlignCenter)
        elif position == TopNavigationItemPosition.RIGHT:
            widget.setParent(self)
            self.rightLayout.insertWidget(
                index, widget, 0, Qt.AlignRight | Qt.AlignVCenter
            )
        else:
            widget.setParent(self.scrollWidget)
            self.scrollLayout.insertWidget(
                index, widget, 0, Qt.AlignLeft | Qt.AlignVCenter
            )

        widget.show()

    def removeWidget(self, routeKey: str):
        """remove widget"""
        if routeKey not in self.items:
            return

        widget = self.items.pop(routeKey)
        widget.deleteLater()
        self.history.remove(routeKey)

    def currentItem(self):
        return self.widget(self._currentRouteKey) if self._currentRouteKey else None

    def setCurrentItem(self, routeKey: str):
        """set current selected item"""
        if routeKey not in self.items or routeKey == self._currentRouteKey:
            return

        # stop current animation and reset position like Pivot
        self._adjustIndicatorPos()

        self._currentRouteKey = routeKey

        # update indicator color
        newItem = self.currentItem()
        if newItem:
            self.lightIndicatorColor = newItem.lightIndicatorColor
            self.darkIndicatorColor = newItem.darkIndicatorColor

        # start animation like Pivot
        if self._isIndicatorAnimationEnabled:
            self.slideAni.startAnimation(self.currentIndicatorGeometry())

        for k, widget in self.items.items():
            widget.setSelected(k == routeKey)

    def currentIndicatorGeometry(self):
        """get current indicator geometry like Pivot"""
        item = self.currentItem()
        if not item:
            return QRectF(0, self.height() - 6, 16, 3)

        rect = item.geometry()
        return QRectF(
            rect.x() - 8 + rect.width() // 2,
            self.height() - 9,
            16,
            3,
        )

    def setIndicatorColor(self, light, dark):
        self.lightIndicatorColor = QColor(light)
        self.darkIndicatorColor = QColor(dark)
        self.update()

    def isIndicatorAnimationEnabled(self):
        return self._isIndicatorAnimationEnabled

    def setIndicatorAnimationEnabled(self, isEnabled: bool):
        self._isIndicatorAnimationEnabled = isEnabled

    def _onWidgetClicked(self):
        widget = self.sender()  # type: NavigationWidget
        if widget.isSelectable:
            self.setCurrentItem(widget.property("routeKey"))

    def _onIndicatorAniFinished(self):
        pass

    def setReturnButtonVisible(self, isVisible: bool):
        self._isReturnButtonVisible = isVisible
        self.returnButton.setVisible(isVisible)

    def layoutMinWidth(self):
        """minimum width for layout"""
        width = 24  # margins
        for item in self.items.values():
            width += item.width() + 4
        return width

    def showEvent(self, e):
        super().showEvent(e)
        self._adjustIndicatorPos()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._adjustIndicatorPos()

    def _adjustIndicatorPos(self):
        item = self.currentItem()
        if item:
            self.slideAni.stop()
            self.slideAni.setValue(self.currentIndicatorGeometry())

    def paintEvent(self, e):
        super().paintEvent(e)

        if not self.currentItem():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(
            autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor)
        )
        painter.drawRoundedRect(self.slideAni.geometry, 1.5, 1.5)


class TopNavigationPushButton(NavigationPushButton):
    """Top navigation push button (horizontal layout)"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        isSelectable: bool,
        parent=None,
    ):
        super().__init__(icon, text, isSelectable, parent)
        self._isExpanded = False  # individual expand state
        self.setFixedSize(40, 36)

    def _canDrawIndicator(self):
        """Don't draw indicator on button - panel handles it"""
        return False

    def setCompacted(self, isCompacted: bool):
        """set whether the widget is compacted (global setting)"""
        # Skip if expanded - expanded items always show text
        if self._isExpanded:
            return

        if isCompacted == self.isCompacted:
            return

        self.isCompacted = isCompacted
        self._updateSize()
        self.update()

    def setExpanded(self, isExpanded: bool):
        """set whether this individual button is expanded (show text)"""
        if self._isExpanded == isExpanded:
            return

        self._isExpanded = isExpanded
        # When expanded, set isCompacted to False so paintEvent draws text
        if isExpanded:
            self.isCompacted = False
        self._updateSize()
        self.update()

    def isExpanded(self):
        """check if this button is individually expanded"""
        return self._isExpanded

    def _updateSize(self):
        """update button size based on expand state"""
        if self._isExpanded or not self.isCompacted:
            # calculate width based on text
            from PySide6.QtGui import QFontMetrics

            fm = QFontMetrics(self.font())
            textWidth = fm.horizontalAdvance(self.text())
            width = max(80, 44 + textWidth + 16)  # icon + text + padding
            self.setFixedSize(width, 36)
        else:
            self.setFixedSize(40, 36)
