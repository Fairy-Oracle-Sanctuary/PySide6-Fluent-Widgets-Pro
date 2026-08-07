from __future__ import annotations

from enum import Enum

from PySide6.QtCore import (
    QEvent,
    QMargins,
    QPoint,
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QWidget

from ...common.animation import ScaleSlideAnimation
from ...common.color import autoFallbackThemeColor
from ...common.icon import FluentIcon as FIF
from ...common.router import qrouter
from ...common.style_sheet import FluentStyleSheet
from ...components.widgets.scroll_area import SingleDirectionScrollArea
from ..widgets.info_badge import InfoBadgeManager, InfoBadgePosition
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
    MENU = 2  # menu mode


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

        self.returnButton = NavigationToolButton(FIF.RETURN, self)

        # 中间区域使用可横向滚动的 ScrollArea 包裹 LEFT 按钮，
        # 类似 FluentWindow 的左侧导航滚动机制：左右固定，中间可滚动。
        # 不再使用 moreButton + overflow 折叠机制，避免 resize 抽搐。
        self.scrollArea = SingleDirectionScrollArea(self, Qt.Horizontal)
        self.scrollWidget = QWidget()

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

        # 配置横向滚动区域：隐藏滚动条，启用可缩放 widget
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.enableTransparentBackground()

        # 滚动时更新指示器和徽章位置 (按钮在 scrollWidget 中，滚动时其 mapTo 坐标会变
        # 但按钮自身不会触发 Move 事件，所以需要主动监听滚动条值变化)
        self.scrollArea.horizontalScrollBar().valueChanged.connect(
            self._onScrollChanged
        )

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

        # 布局结构: [返回按钮 | LEFT按钮(可横向滚动) | CENTER按钮 | RIGHT按钮]
        # - leftLayout: 返回按钮 (固定，不参与滚动)
        # - scrollArea: LEFT 位置按钮 (超出宽度时横向滚动)
        # - centerLayout: CENTER 位置按钮 (固定居中)
        # - rightLayout: RIGHT 位置按钮 (固定靠右)
        self.hBoxLayout.addLayout(self.leftLayout)
        self.hBoxLayout.addWidget(self.scrollArea, 1)
        self.hBoxLayout.addLayout(self.centerLayout)
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
        icon,
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
        icon,
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
            widget.setParent(self.scrollWidget)
            self.scrollLayout.insertWidget(
                index, widget, 0, Qt.AlignLeft | Qt.AlignVCenter
            )
        elif position == TopNavigationItemPosition.CENTER:
            widget.setParent(self)
            self.centerLayout.insertWidget(index, widget, 0, Qt.AlignCenter)
        elif position == TopNavigationItemPosition.RIGHT:
            widget.setParent(self)
            if index < 0:
                index = self.rightLayout.count()
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

            # 如果目标按钮在滚动区域内，自动滚动到可见位置
            # (返回按钮跳转、程序化切换路由时，目标按钮可能被滚出视口)
            # ensureWidgetVisible 会同步触发 valueChanged → _onScrollChanged → 更新徽章位置
            if newItem.parent() is self.scrollWidget:
                self.scrollArea.ensureWidgetVisible(newItem, 50, 0)

        # start animation like Pivot
        # 注意：必须在 ensureWidgetVisible 之后调用，这样 currentIndicatorGeometry
        # 使用的 mapTo 坐标才是基于滚动后的正确位置
        if self._isIndicatorAnimationEnabled:
            self.slideAni.startAnimation(self.currentIndicatorGeometry())

        for k, widget in self.items.items():
            widget.setSelected(k == routeKey)

    def currentIndicatorGeometry(self):
        """get current indicator geometry like Pivot"""
        item = self.currentItem()
        if not item or not item.isVisible():
            return QRectF(0, self.height() - 6, 16, 3)

        topLeft = item.mapTo(self, QPoint(0, 0))
        rect = QRectF(topLeft.x(), topLeft.y(), item.width(), item.height())
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

    def _onScrollChanged(self):
        """滚动条值变化时，更新指示器和所有徽章的位置。

        按钮在 scrollWidget 中，滚动时按钮自身的 geometry 不变 (是 viewport 在动)，
        所以按钮不会触发 Move 事件，InfoBadgeManager 的 eventFilter 捕获不到。
        这里主动遍历所有按钮，调用 InfoBadgeManager.updateForTarget 重定位徽章。
        """
        # 1. 更新指示器位置 (基于 mapTo，会自动包含滚动偏移)
        self._adjustIndicatorPos()

        # 2. 更新所有按钮上的徽章位置
        for item in self.items.values():
            InfoBadgeManager.updateForTarget(item)

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
        icon,
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

    def _margins(self):
        """compact 模式下补偿 icon 位置，使其在按钮中更居中

        父类 paintEvent 的 icon x = 11.5 + pl，为侧边栏左对齐设计。
        compact 模式（仅 icon）时加 1px 补偿，与 NavigationToolButton 一致。
        expanded 模式保持 0，icon 左对齐为文字留空间。
        """
        if self.isCompacted and not self._isExpanded:
            return QMargins(1, 0, 0, 0)
        return QMargins(0, 0, 0, 0)

    def _iconXOffset(self):
        """expanded 模式（icon+text）下 icon 向右偏移 2px，文字位置保持不变"""
        if self._isExpanded or not self.isCompacted:
            return 7
        return 0

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


@InfoBadgeManager.register(InfoBadgePosition.TOP_NAVIGATION_ITEM)
class TopNavigationItemInfoBadgeManager(InfoBadgeManager):
    """Info badge manager dedicated to TopNavigationPushButton.

    根据 target 自身的长宽 + 文字宽度动态计算徽章位置：
    - compact 模式（仅图标）：徽章中心对齐到按钮图标右上角
    - expanded 模式（图标+文字）：徽章中心对齐到「文字右边缘 + 偏移」，y 贴在按钮顶部

    与按钮文字内容无关，改文字无需调整代码。
    badge 的 parent 可能与 target 的 parent 不同（target 在 scrollWidget 里，
    badge 挂在 navigationInterface 上），所以使用 mapTo 做坐标映射。
    """

    # 与 NavigationPushButton.paintEvent 中保持一致的常量
    ICON_LEFT = 11.5  # 图标左边缘 x
    ICON_SIZE = 16  # 图标尺寸
    ICON_TOP = 7  # 图标顶部 y
    TEXT_LEFT_OFFSET = 44  # 文本左边缘相对于按钮左边的偏移 (含 icon + padding)
    BADGE_OFFSET = 10  # 徽章超出文字右边缘的偏移量

    def eventFilter(self, obj, e: QEvent):
        """target 显示时也触发一次定位，确保首次显示徽章在正确位置"""
        if obj is self.target and e.type() == QEvent.Show:
            self.badge.move(self.position())
        return super().eventFilter(obj, e)

    def position(self):
        target = self.target
        badge = self.badge

        # badge 的 parent 可能与 target 的 parent 不同
        # (TopFluentWindow 中 target 在 scrollWidget 里，badge 挂在 navigationInterface 上)
        # 所以必须把 target 的局部坐标映射到 badge 的 parent 坐标系
        parent = badge.parent()
        if parent is None:
            return QPoint()

        # 判断按钮是否在滚动区域的可视范围内
        # 按钮在 scrollWidget 中，滚动出视口时 isVisible() 仍为 True (只是被 viewport 裁剪)，
        # 需要额外检查按钮映射到 scrollArea viewport 后是否与可视矩形相交
        # 向上遍历父级定位到 scrollArea (target.parent() = scrollWidget,
        # scrollWidget.parent() = scrollArea)
        p = target.parent()
        sa = None
        while p is not None:
            # 用 QAbstractScrollArea 的特征判断
            if hasattr(p, "horizontalScrollBar") and hasattr(p, "viewport"):
                sa = p
                break
            p = p.parent()

        visible = target.isVisible()
        if visible and sa is not None:
            # 按钮映射到 scrollArea viewport 的矩形
            viewRect = sa.viewport().rect()
            targetRect = QRectF(
                target.mapTo(sa.viewport(), QPoint(0, 0)),
                target.size(),
            )
            # 不相交则隐藏徽章
            if not viewRect.intersects(targetRect.toRect()):
                visible = False

        self.badge.setVisible(visible)

        # 不可见时不需要更新位置，返回当前即可
        if not visible:
            return badge.pos()

        # 取按钮的 _margins()，与 paintEvent 一致
        m = target._margins() if hasattr(target, "_margins") else QMargins(0, 0, 0, 0)
        pl = m.left()

        # compact 模式：仅图标，徽章中心对齐图标右上角
        if getattr(target, "isCompacted", True):
            iconRight = self.ICON_LEFT + pl + self.ICON_SIZE
            localPos = QPoint(
                int(iconRight - badge.width() / 2),
                int(self.ICON_TOP - badge.height() / 2),
            )
            return target.mapTo(parent, localPos)

        # expanded 模式：徽章中心对齐到「文字右边缘 + 偏移」
        # 文本左边缘 x 坐标 (相对 target)
        textLeftX = self.TEXT_LEFT_OFFSET + pl
        # 实际文字宽度（动态计算，与具体文字内容无关）
        textWidth = QFontMetrics(target.font()).horizontalAdvance(target.text())
        # 文字右边缘 x 坐标 (相对 target)
        textRightX = textLeftX + textWidth

        # y 坐标对齐到图标顶部 (与 compact 模式一致)，让徽章贴在按钮右上角
        localPos = QPoint(
            int(textRightX + self.BADGE_OFFSET - badge.width() / 2),
            int(self.ICON_TOP - badge.height() / 2),
        )
        return target.mapTo(parent, localPos)


TopNavigationBar = TopNavigationPanel
