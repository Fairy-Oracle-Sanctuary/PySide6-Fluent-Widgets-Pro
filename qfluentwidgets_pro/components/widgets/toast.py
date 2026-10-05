# coding:utf-8
from __future__ import annotations

from enum import Enum
from typing import List, Union

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    QSize,
    QRectF,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from ...common.auto_wrap import TextWrap
from ...common.font import setFont
from ...common.config import qconfig
from ...common.icon import FluentIcon, isDarkTheme
from ...common.style_sheet import themeColor
from .button import TransparentToolButton
from .label import BodyLabel


class ToastColor(Enum):
    """toast infoBar color"""

    SUCCESS = "#0F7B0F"
    ERROR = "#BC0E11"
    WARNING = "#FCE100"

    def __new__(cls, color):
        obj = object.__new__(cls)
        obj.color = QColor(color)
        return obj

    @property
    def value(self):
        return self.color


class ToastPosition(Enum):
    """toast infoBar position"""

    TOP = 0
    BOTTOM = 1
    TOP_LEFT = 2
    TOP_RIGHT = 3
    BOTTOM_LEFT = 4
    BOTTOM_RIGHT = 5


class Toast(QFrame):
    """toast infoBar"""

    closed = Signal()

    def __init__(
        self,
        title: str,
        content: str,
        duration: int,
        isClosable: bool,
        position: ToastPosition,
        orient: Qt.Orientation,
        toastColor: Union[str, QColor, ToastColor],
        parent: QWidget,
        backgroundColor: QColor = None,
        useThemeColor: bool = False,
    ):
        if parent is None:
            raise ValueError('Toast requires a parent widget')
        super().__init__(parent)
        parent.installEventFilter(self)
        self.title: str = title
        self.content: str = content
        self.duration: int = duration
        self.isCloseable: bool = isClosable
        self.orient: Qt.Orientation = orient
        self.toastColor: QColor = (
            QColor(toastColor.value) if isinstance(toastColor, ToastColor)
            else QColor(toastColor)
        )
        self.position: ToastPosition = position
        self.backgroundColor: QColor = backgroundColor
        self._useThemeColor: bool = useThemeColor

        self.titleLabel: BodyLabel = BodyLabel(self)
        self.contentLabel: BodyLabel = BodyLabel(self)
        self.closeButton: TransparentToolButton = TransparentToolButton(
            FluentIcon.CLOSE, self
        )

        self.hBoxLayout: QHBoxLayout = QHBoxLayout(self)
        if orient == Qt.Horizontal:
            self.textLayout: QHBoxLayout = QHBoxLayout()
            self.widgetLayout: QHBoxLayout = QHBoxLayout()
        else:
            self.textLayout: QVBoxLayout = QVBoxLayout()
            self.widgetLayout: QVBoxLayout = QVBoxLayout()

        self.__posAni: QPropertyAnimation = QPropertyAnimation(self, b"pos")
        self.__posAni.setEasingCurve(QEasingCurve.OutQuad)
        self.__posAni.setDuration(200)
        self._closeTimer = QTimer(self)
        self._closeTimer.setSingleShot(True)
        self._closeTimer.timeout.connect(self.close)
        qconfig.themeChangedFinished.connect(self.update)
        qconfig.themeColorChanged.connect(self.update)

        self._adjustText()
        self.__initWidget()
        self.__initShadowEffect()
        self.manager: ToastManager = ToastManager.get(self.position)

    def __initWidget(self):
        self.closeButton.setFixedSize(28, 28)
        self.closeButton.setIconSize(QSize(12, 12))
        self.closeButton.setCursor(Qt.PointingHandCursor)
        self.closeButton.setVisible(self.isCloseable)
        self.closeButton.clicked.connect(self.close)

        setFont(self.titleLabel, 13, QFont.DemiBold)
        setFont(self.contentLabel)
        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(20, 18, 16, 16)
        self.hBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.textLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        self.textLayout.setAlignment(Qt.AlignTop)
        self.textLayout.setContentsMargins(0, 0, 0, 0)

        self.hBoxLayout.setSpacing(0)
        self.textLayout.setSpacing(10)

        self.textLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.titleLabel.setVisible(bool(self.title))

        if self.orient == Qt.Horizontal:
            self.textLayout.addSpacing(7)

        self.textLayout.addWidget(self.contentLabel, 1, Qt.AlignTop)
        self.contentLabel.setVisible(bool(self.content))
        self.hBoxLayout.addLayout(self.textLayout)

        if self.orient == Qt.Horizontal:
            self.hBoxLayout.addLayout(self.widgetLayout)
            self.widgetLayout.setSpacing(10)
        else:
            self.textLayout.addLayout(self.widgetLayout)

        self.hBoxLayout.addSpacing(12)
        self.hBoxLayout.addWidget(self.closeButton, 0, Qt.AlignTop | Qt.AlignLeft)

    def __initShadowEffect(self):
        self.shadowEffect: QGraphicsDropShadowEffect = QGraphicsDropShadowEffect(self)
        self.shadowEffect.setBlurRadius(24)
        self.shadowEffect.setOffset(0, 6)
        self.shadowEffect.setColor(QColor(0, 0, 0, 64))
        self.setGraphicsEffect(self.shadowEffect)

    def run(self):
        self.__posAni.setStartValue(self.startPosition)
        self.__posAni.setEndValue(self.endPosition)
        self.__posAni.start()

    def _adjustText(self):
        width = self.parent().width() / 1.5

        chars = max(min(width / 10, 120), 30)
        self.titleLabel.setText(TextWrap.wrap(self.title, chars, False)[0])

        chars = max(min(width / 9, 120), 30)
        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])
        self.adjustSize()

    @classmethod
    def new(
        cls,
        title: str,
        content: str,
        duration: int,
        isClosable: bool,
        position: ToastPosition,
        orient=Qt.Vertical,
        toastColor: Union[str, QColor, ToastColor] = ToastColor.SUCCESS,
        parent: QWidget = None,
        backgroundColor: QColor = None,
        useThemeColor: bool = False,
    ):
        toastInfoBar = cls(
            title,
            content,
            duration,
            isClosable,
            position,
            orient,
            toastColor,
            parent,
            backgroundColor,
            useThemeColor,
        )
        toastInfoBar.show()
        return toastInfoBar

    @classmethod
    def info(
        cls,
        title: str,
        content: str,
        duration: int = 2000,
        isClosable: bool = True,
        position: ToastPosition = ToastPosition.TOP_RIGHT,
        orient: Qt.Orientation = Qt.Vertical,
        parent: QWidget = None,
    ):
        return cls.new(
            title,
            content,
            duration,
            isClosable,
            position,
            orient,
            themeColor(),
            parent,
            useThemeColor=True,
        )

    @classmethod
    def success(
        cls,
        title: str,
        content: str,
        duration: int = 2000,
        isClosable: bool = True,
        position: ToastPosition = ToastPosition.TOP_RIGHT,
        orient=Qt.Vertical,
        parent: QWidget = None,
    ):
        return cls.new(
            title,
            content,
            duration,
            isClosable,
            position,
            orient,
            ToastColor.SUCCESS.value,
            parent,
        )

    @classmethod
    def warning(
        cls,
        title: str,
        content: str,
        duration: int = 2000,
        isClosable: bool = True,
        position: ToastPosition = ToastPosition.TOP_RIGHT,
        orient=Qt.Vertical,
        parent: QWidget = None,
    ):
        return cls.new(
            title,
            content,
            duration,
            isClosable,
            position,
            orient,
            ToastColor.WARNING.value,
            parent,
        )

    @classmethod
    def error(
        cls,
        title: str,
        content: str,
        duration: int = -1,
        isClosable: bool = True,
        position: ToastPosition = ToastPosition.TOP_RIGHT,
        orient=Qt.Vertical,
        parent: QWidget = None,
    ):
        return cls.new(
            title,
            content,
            duration,
            isClosable,
            position,
            orient,
            ToastColor.ERROR.value,
            parent,
        )

    @classmethod
    def custom(
        cls,
        title: str,
        content: str,
        duration: int = 2000,
        isClosable: bool = True,
        position: ToastPosition = ToastPosition.TOP_RIGHT,
        orient=Qt.Vertical,
        parent: QWidget = None,
        toastColor: Union[str, QColor] = None,
        backgroundColor: QColor = None,
    ):
        return cls.new(
            title,
            content,
            duration,
            isClosable,
            position,
            orient,
            toastColor,
            parent,
            backgroundColor,
        )

    def addWidget(self, widget: QWidget, stretch=0, alignment=Qt.AlignLeft):
        self.widgetLayout.addSpacing(6)
        self.widgetLayout.addWidget(widget, stretch, alignment)
        self.adjustSize()

    def show(self):
        self._adjustText()
        super().show()
        self.manager.add(self)
        self.startPosition = self.manager.slideStartPos(self)
        self.endPosition = self.manager.slideEndPos(self)
        self.run()

        if self.duration >= 0:
            self._closeTimer.start(self.duration)

    def closeEvent(self, event):
        self._closeTimer.stop()
        self.__posAni.stop()
        self.manager.remove(self)
        self.parent().removeEventFilter(self)
        self.deleteLater()
        super().closeEvent(event)
        self.closed.emit()

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type() in [
            QEvent.Resize,
            QEvent.WindowStateChange,
        ]:
            try:
                self._adjustText()
                self.move(self.manager.slideEndPos(self))
            except Exception:
                ...
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # Use theme color for INFO type
        if self._useThemeColor:
            painter.setBrush(themeColor())
        else:
            painter.setBrush(self.toastColor)

        statusColor = painter.brush().color()
        w, h = self.width(), self.height()
        shape = QPainterPath()
        shape.addRoundedRect(QRectF(0, 0, w, h), 8, 8)
        painter.setClipPath(shape)
        painter.setBrush(
            self.backgroundColor
            or (QColor("#323232") if isDarkTheme() else QColor("#F2F2F2"))
        )
        painter.drawRect(QRectF(0, 0, w, h))
        painter.fillRect(QRectF(0, 0, w, 4), statusColor)


class ToastManager(QObject):
    """Toast manager"""

    _instances = {}
    registry = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super(ToastManager, cls).__new__(cls)
            instance.__initialized = False
            cls._instances[cls] = instance
        return cls._instances[cls]

    def __init__(self):
        if self.__initialized:
            return
        super().__init__()
        self.margin: int = 24
        self.toastInfoBars: List[Toast] = []
        self.__initialized: bool = True

    def add(self, infoBar: Toast):
        if infoBar in self.toastInfoBars:
            return
        self.toastInfoBars.append(infoBar)
        infoBar.destroyed.connect(lambda *_: self._forgetDestroyed(infoBar))

    def _forgetDestroyed(self, infoBar):
        if infoBar in self.toastInfoBars:
            self.toastInfoBars.remove(infoBar)

    def _precedingBars(self, infoBar):
        return [bar for bar in self.toastInfoBars[:self.toastInfoBars.index(infoBar)]
                if bar.parent() is infoBar.parent()]

    def remove(self, infoBar: Toast):
        if infoBar not in self.toastInfoBars:
            return
        self.toastInfoBars.remove(infoBar)
        self._adjustPosition()

    def _adjustPosition(self):
        for bar in self.toastInfoBars:
            bar.startPosition, bar.endPosition = bar.pos(), self.slideEndPos(bar)
            bar.run()

    @classmethod
    def register(cls, element):
        def decorator(classType):
            cls.registry[element] = classType
            return classType

        return decorator

    @classmethod
    def get(cls, operation):
        if operation not in cls.registry:
            raise ValueError(f"No operation registered for {operation}")
        return cls.registry[operation]()

    def slideStartPos(self, toastInfoBar: Toast) -> QPoint:
        raise NotImplementedError

    def slideEndPos(self, toastInfoBar: Toast) -> QPoint:
        raise NotImplementedError


@ToastManager.register(ToastPosition.TOP)
class TopToastManager(ToastManager):
    def slideEndPos(self, toastInfoBar):
        x = (toastInfoBar.parent().width() - toastInfoBar.width()) // 2
        y = self.margin / 2.5
        for bar in self._precedingBars(toastInfoBar):
            y += bar.height() + self.margin
        return QPoint(round(x), round(y + self.margin))

    def slideStartPos(self, toastInfoBar) -> QPoint:
        pos = self.slideEndPos(toastInfoBar)
        return QPoint(pos.x(), pos.y() - toastInfoBar.height() // 4)


@ToastManager.register(ToastPosition.TOP_LEFT)
class TopLeftToastManager(ToastManager):
    def slideEndPos(self, toastInfoBar):
        x = self.margin
        y = self.margin / 2.5
        for bar in self._precedingBars(toastInfoBar):
            y += bar.height() + self.margin
        return QPoint(round(x), round(y + self.margin))

    def slideStartPos(self, toastInfoBar: Toast) -> QPoint:
        pos = self.slideEndPos(toastInfoBar)
        return QPoint(-toastInfoBar.width(), pos.y())


@ToastManager.register(ToastPosition.TOP_RIGHT)
class TopRightToastManager(ToastManager):
    def slideEndPos(self, toastInfoBar):
        x = toastInfoBar.parent().width() - toastInfoBar.width() - self.margin
        y = self.margin / 2.5
        for bar in self._precedingBars(toastInfoBar):
            y += bar.height() + self.margin
        return QPoint(round(x), round(y + self.margin))

    def slideStartPos(self, toastInfoBar: Toast) -> QPoint:
        pos = self.slideEndPos(toastInfoBar)
        return QPoint(toastInfoBar.parent().width() + toastInfoBar.width(), pos.y())


@ToastManager.register(ToastPosition.BOTTOM)
class BottomToastManager(ToastManager):
    def slideEndPos(self, toastInfoBar):
        parent = toastInfoBar.parent()
        x = (parent.width() - toastInfoBar.width()) // 2
        y = parent.height() - self.margin
        for bar in self._precedingBars(toastInfoBar):
            y -= bar.height() + self.margin
        return QPoint(x, y - toastInfoBar.height())

    def slideStartPos(self, toastInfoBar: Toast) -> QPoint:
        pos = self.slideEndPos(toastInfoBar)
        return QPoint(pos.x(), pos.y() + toastInfoBar.height() // 4)


@ToastManager.register(ToastPosition.BOTTOM_LEFT)
class BottomLeftToastManager(ToastManager):
    def slideEndPos(self, toastInfoBar):
        x = self.margin
        y = toastInfoBar.parent().height() - self.margin
        for bar in self._precedingBars(toastInfoBar):
            y -= bar.height() + self.margin
        return QPoint(x, y - toastInfoBar.height())

    def slideStartPos(self, toastInfoBar: Toast) -> QPoint:
        pos = self.slideEndPos(toastInfoBar)
        return QPoint(-toastInfoBar.width(), pos.y())


@ToastManager.register(ToastPosition.BOTTOM_RIGHT)
class BottomRightToastManager(ToastManager):
    def slideEndPos(self, toastInfoBar):
        parent = toastInfoBar.parent()
        x = parent.width() - toastInfoBar.width() - self.margin
        y = parent.height() - self.margin
        for bar in self._precedingBars(toastInfoBar):
            y -= bar.height() + self.margin
        return QPoint(x, y - toastInfoBar.height())

    def slideStartPos(self, toastInfoBar: Toast) -> QPoint:
        pos = self.slideEndPos(toastInfoBar)
        return QPoint(toastInfoBar.parent().width() + self.margin, pos.y())
