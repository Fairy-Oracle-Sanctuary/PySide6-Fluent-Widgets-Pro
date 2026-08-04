from __future__ import annotations

from PySide6.QtCore import Property, QPoint, QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...common.animation import BackgroundAnimationWidget, DropShadowAnimation
from ...common.font import setFont
from ...common.icon import FluentIconBase
from ...common.overload import singledispatchmethod
from ...common.style_sheet import FluentStyleSheet, isDarkTheme
from .icon_widget import IconWidget
from .label import BodyLabel, CaptionLabel


class CardWidget(BackgroundAnimationWidget, QFrame):
    """Card widget"""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._isClickEnabled = False
        self._borderRadius = 5

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def setClickEnabled(self, isEnabled: bool):
        self._isClickEnabled = isEnabled
        self.update()

    def isClickEnabled(self):
        return self._isClickEnabled

    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _hoverBackgroundColor(self):
        return QColor(255, 255, 255, 21 if isDarkTheme() else 64)

    def _pressedBackgroundColor(self):
        return QColor(255, 255, 255, 8 if isDarkTheme() else 64)

    def getBorderRadius(self):
        return self._borderRadius

    def setBorderRadius(self, radius: int):
        self._borderRadius = radius
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        r = self.borderRadius
        d = 2 * r

        isDark = isDarkTheme()

        # draw top border
        path = QPainterPath()
        # path.moveTo(1, h - r)
        path.arcMoveTo(1, h - d - 1, d, d, 240)
        path.arcTo(1, h - d - 1, d, d, 225, -60)
        path.lineTo(1, r)
        path.arcTo(1, 1, d, d, -180, -90)
        path.lineTo(w - r, 1)
        path.arcTo(w - d - 1, 1, d, d, 90, -90)
        path.lineTo(w - 1, h - r)
        path.arcTo(w - d - 1, h - d - 1, d, d, 0, -60)

        topBorderColor = QColor(0, 0, 0, 20)
        if isDark:
            if self.isPressed:
                topBorderColor = QColor(255, 255, 255, 18)
            elif self.isHover:
                topBorderColor = QColor(255, 255, 255, 13)
        else:
            topBorderColor = QColor(0, 0, 0, 15)

        painter.strokePath(path, topBorderColor)

        # draw bottom border
        path = QPainterPath()
        path.arcMoveTo(1, h - d - 1, d, d, 240)
        path.arcTo(1, h - d - 1, d, d, 240, 30)
        path.lineTo(w - r - 1, h - 1)
        path.arcTo(w - d - 1, h - d - 1, d, d, 270, 30)

        bottomBorderColor = topBorderColor
        if not isDark and self.isHover and not self.isPressed:
            bottomBorderColor = QColor(0, 0, 0, 27)

        painter.strokePath(path, bottomBorderColor)

        # draw background
        painter.setPen(Qt.NoPen)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(self.backgroundColor)
        painter.drawRoundedRect(rect, r, r)

    borderRadius = Property(int, getBorderRadius, setBorderRadius)


class SimpleCardWidget(CardWidget):
    """Simple card widget"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _hoverBackgroundColor(self):
        return self._normalBackgroundColor()

    def _pressedBackgroundColor(self):
        return self._normalBackgroundColor()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setBrush(self.backgroundColor)

        if isDarkTheme():
            painter.setPen(QColor(0, 0, 0, 48))
        else:
            painter.setPen(QColor(0, 0, 0, 12))

        r = self.borderRadius
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)


class ElevatedCardWidget(SimpleCardWidget):
    """Card widget with shadow effect"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.shadowAni = DropShadowAnimation(self, hoverColor=QColor(0, 0, 0, 20))
        self.shadowAni.setOffset(0, 5)
        self.shadowAni.setBlurRadius(38)

        self.elevatedAni = QPropertyAnimation(self, b"pos", self)
        self.elevatedAni.setDuration(100)

        self._originalPos = self.pos()
        self.setBorderRadius(8)

    def enterEvent(self, e):
        super().enterEvent(e)

        if self.elevatedAni.state() != QPropertyAnimation.Running:
            self._originalPos = self.pos()

        self._startElevateAni(self.pos(), self.pos() - QPoint(0, 3))

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._startElevateAni(self.pos(), self._originalPos)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self._startElevateAni(self.pos(), self._originalPos)

    def _startElevateAni(self, start, end):
        self.elevatedAni.setStartValue(start)
        self.elevatedAni.setEndValue(end)
        self.elevatedAni.start()

    def _hoverBackgroundColor(self):
        return QColor(255, 255, 255, 16) if isDarkTheme() else QColor(255, 255, 255)

    def _pressedBackgroundColor(self):
        return QColor(255, 255, 255, 6 if isDarkTheme() else 118)


class CardSeparator(QWidget):
    """Card separator"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(3)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255, 46))
        else:
            painter.setPen(QColor(0, 0, 0, 12))

        painter.drawLine(2, 1, self.width() - 2, 1)


class HeaderCardWidget(SimpleCardWidget):
    """Header card widget"""

    @singledispatchmethod
    def __init__(self, parent=None):
        super().__init__(parent)
        self.headerView = QWidget(self)
        self.headerLabel = QLabel(self)
        self.separator = CardSeparator(self)
        self.view = QWidget(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.headerLayout = QHBoxLayout(self.headerView)
        self.viewLayout = QHBoxLayout(self.view)

        self.headerLayout.addWidget(self.headerLabel)
        self.headerLayout.setContentsMargins(24, 0, 16, 0)
        self.headerView.setFixedHeight(48)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.headerView)
        self.vBoxLayout.addWidget(self.separator)
        self.vBoxLayout.addWidget(self.view)

        self.viewLayout.setContentsMargins(24, 24, 24, 24)
        setFont(self.headerLabel, 15, QFont.DemiBold)

        self.view.setObjectName("view")
        self.headerView.setObjectName("headerView")
        self.headerLabel.setObjectName("headerLabel")
        FluentStyleSheet.CARD_WIDGET.apply(self)

        self._postInit()

    @__init__.register
    def _(self, title: str, parent=None):
        self.__init__(parent)
        self.setTitle(title)

    def getTitle(self):
        return self.headerLabel.text()

    def setTitle(self, title: str):
        self.headerLabel.setText(title)

    def _postInit(self):
        pass

    title = Property(str, getTitle, setTitle)


class CardGroupWidget(QWidget):
    def __init__(
        self,
        icon: str | FluentIconBase | QIcon,
        title: str,
        content: str,
        parent=None,
    ):
        super().__init__(parent=parent)
        self._wordWrapExtraHeight = 0  # wordWrap 导致 sizeHint 虚高的高度
        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout()

        self.iconWidget = IconWidget(icon)
        self.titleLabel = BodyLabel(title)
        self.contentLabel = CaptionLabel(content)
        self.textLayout = QVBoxLayout()

        self.separator = CardSeparator()

        self.__initWidget()

    def __initWidget(self):
        self.separator.hide()
        self.iconWidget.setFixedSize(20, 20)
        self.contentLabel.setTextColor(QColor(96, 96, 96), QColor(206, 206, 206))

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.hBoxLayout)
        self.vBoxLayout.addWidget(self.separator)

        self.textLayout.addWidget(self.titleLabel)
        self.textLayout.addWidget(self.contentLabel)
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.textLayout)
        self.hBoxLayout.addStretch(1)

        self.hBoxLayout.setSpacing(15)
        self.hBoxLayout.setContentsMargins(24, 10, 24, 10)
        self.textLayout.setContentsMargins(0, 0, 0, 0)
        self.textLayout.setSpacing(0)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.textLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def title(self):
        return self.titleLabel.text()

    def setTitle(self, text: str):
        self.titleLabel.setText(text)

    def content(self):
        return self.contentLabel.text()

    def setContent(self, text: str):
        self.contentLabel.setText(text)

    def setContentWordWrap(self, enable: bool):
        """设置 contentLabel 是否启用自动换行

        ## wordWrap 虚高问题

        QLabel 开启 wordWrap 后，``sizeHint().height()`` 按最窄宽度计算
        （即两行高度），但实际在足够宽的容器中通常只显示一行。这个偏大的
        sizeHint 会导致父布局 ``CardGroupWidget`` 的 sizeHint/minimumSizeHint
        虚高，在以下场景产生问题：

        1. **卡片间距异常**：多个 group 的虚高累加，QVBoxLayout 按 sizeHint
           分配空间，导致某些卡片之间出现远大于 spacing 的空隙。
        2. **QStackedWidget 锁高后撑大**：外层用 ``setFixedHeight`` 锁定页面
           高度后，多余空间会分发给 sizeHint 偏大的 group，进一步放大间距。

        ## 修复策略

        - 步骤 1-4：调整 sizePolicy 和 stretch，让 contentLabel 拿到足够宽度
          尽量单行显示，避免过早换行。
        - 步骤 5：计算 wordWrap 虚高差值 ``_wordWrapExtraHeight``，在重写的
          ``sizeHint``/``minimumSizeHint`` 中扣除，使布局按真实单行高度分配。

        ## 已知局限

        ``_wordWrapExtraHeight`` 是一次性静态计算的（基于调用时的 QLabel 宽度）。
        若后续容器宽度变化导致实际换行数改变，差值不会自动更新，可能出现轻微
        偏差。配合 ``QVBoxLayout.addStretch()`` 可让多余空间被弹簧吸收而非分给
        group，作为这一局限的兜底方案。
        """
        self.contentLabel.setWordWrap(enable)
        if enable:
            # 1. contentLabel 水平 Expanding，拿到 textLayout 全部宽度
            sp = self.contentLabel.sizePolicy()
            sp.setHorizontalPolicy(QSizePolicy.Expanding)
            sp.setVerticalPolicy(QSizePolicy.Minimum)
            self.contentLabel.setSizePolicy(sp)
            # 2. 移除弹簧，让 textLayout 独占剩余宽度（而非和弹簧平分）
            for i in range(self.hBoxLayout.count()):
                item = self.hBoxLayout.itemAt(i)
                if item.spacerItem():
                    self.hBoxLayout.takeAt(i)
                    break
            # 3. textLayout stretch=1 拿走全部剩余空间，把 widget 顶到最右
            self.hBoxLayout.setStretchFactor(self.textLayout, 1)
            # 4. 设 widget 水平 Maximum 防止被拉伸
            for i in range(self.hBoxLayout.count()):
                item = self.hBoxLayout.itemAt(i)
                if item.widget() and item.widget() is not self.iconWidget:
                    wsp = item.widget().sizePolicy()
                    wsp.setHorizontalPolicy(QSizePolicy.Maximum)
                    item.widget().setSizePolicy(wsp)
            # 4. wordWrap=True 时 sizeHint.height 按最窄宽度（两行）计算，
            #    实际通常单行。重写 sizeHint/minimumSizeHint 扣除虚高差值，
            #    不限制 contentLabel 实际高度，避免裁剪。
            self.contentLabel.setWordWrap(False)
            single_h = self.contentLabel.sizeHint().height()
            self.contentLabel.setWordWrap(True)
            wrap_h = self.contentLabel.sizeHint().height()
            self._wordWrapExtraHeight = max(0, wrap_h - single_h)
        else:
            self._wordWrapExtraHeight = 0

    def sizeHint(self):
        hint = super().sizeHint()
        if self._wordWrapExtraHeight > 0:
            hint.setHeight(max(0, hint.height() - self._wordWrapExtraHeight))
        return hint

    def minimumSizeHint(self):
        hint = super().minimumSizeHint()
        if self._wordWrapExtraHeight > 0:
            hint.setHeight(max(0, hint.height() - self._wordWrapExtraHeight))
        return hint

    def icon(self):
        return self.iconWidget.icon

    def setIcon(self, icon: str | FluentIconBase | QIcon):
        self.iconWidget.setIcon(icon)

    def setIconSize(self, size: QSize):
        self.iconWidget.setFixedSize(size)

    def setSeparatorVisible(self, isVisible: bool):
        self.separator.setVisible(isVisible)

    def isSeparatorVisible(self):
        return self.separator.isVisible()

    def addWidget(self, widget: QWidget, stretch=0):
        self.hBoxLayout.addWidget(widget, stretch=stretch)


class GroupHeaderCardWidget(HeaderCardWidget):
    """Group header card widget"""

    def _postInit(self):
        super()._postInit()
        self.groupWidgets = []  # type: List[CardGroupWidget]
        self.groupLayout = QVBoxLayout()

        self.groupLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.groupLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.addLayout(self.groupLayout)

    def addGroup(
        self,
        icon: str | FluentIconBase | QIcon,
        title: str,
        content: str,
        widget: QWidget,
        stretch=0,
        wordWrap=False,
    ) -> CardGroupWidget:
        """add widget to a new group

        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        widget: QWidget
            the widget to be added

        stretch: int
            the layout stretch of widget

        wordWrap: bool
            whether to enable word wrap for contentLabel
        """
        group = CardGroupWidget(icon, title, content, self)
        group.setContentWordWrap(wordWrap)
        group.addWidget(widget, stretch=stretch)

        if self.groupWidgets:
            self.groupWidgets[-1].setSeparatorVisible(True)

        self.groupLayout.addWidget(group)
        self.groupWidgets.append(group)
        return group

    def groupCount(self):
        return len(self.groupWidgets)
