# coding:utf-8
from PySide6.QtCore import (
    Property,
    QPoint,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QProxyStyle,
    QSizePolicy,
    QSlider,
    QStyle,
    QStyleOptionSlider,
    QWidget,
)

from ...common.color import autoFallbackThemeColor
from ...common.overload import singledispatchmethod
from ...common.style_sheet import isDarkTheme
from .tool_tip import ToolTip


class SliderHandle(QWidget):
    """Slider handle"""

    pressed = Signal()
    released = Signal()

    def __init__(self, parent: QSlider):
        super().__init__(parent=parent)
        self.setFixedSize(22, 22)
        self._radius = 5
        self.lightHandleColor = QColor()
        self.darkHandleColor = QColor()
        self.radiusAni = QPropertyAnimation(self, b"radius", self)
        self.radiusAni.setDuration(100)

    @Property(int)
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, r):
        self._radius = r
        self.update()

    def setHandleColor(self, light, dark):
        self.lightHandleColor = QColor(light)
        self.darkHandleColor = QColor(dark)
        self.update()

    def enterEvent(self, e):
        self._startAni(6)

    def leaveEvent(self, e):
        self._startAni(5)

    def mousePressEvent(self, e):
        self._startAni(4)
        self.pressed.emit()

    def mouseReleaseEvent(self, e):
        self._startAni(6)
        self.released.emit()

    def _startAni(self, radius):
        self.radiusAni.stop()
        self.radiusAni.setStartValue(self.radius)
        self.radiusAni.setEndValue(radius)
        self.radiusAni.start()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        # draw outer circle
        isDark = isDarkTheme()
        painter.setPen(QColor(0, 0, 0, 90 if isDark else 25))
        painter.setBrush(QColor(69, 69, 69) if isDark else Qt.GlobalColor.white)
        painter.drawEllipse(self.rect().adjusted(1, 1, -1, -1))

        # draw innert circle
        painter.setBrush(
            autoFallbackThemeColor(self.lightHandleColor, self.darkHandleColor)
        )
        painter.drawEllipse(QPoint(11, 11), self.radius, self.radius)


class Slider(QSlider):
    """A slider can be clicked

    Constructors
    ------------
    * Slider(`parent`: QWidget = None)
    * Slider(`orient`: Qt.Orientation, `parent`: QWidget = None)
    """

    clicked = Signal(int)

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._postInit()

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent: QWidget = None):
        super().__init__(orientation, parent=parent)
        self._postInit()

    def _postInit(self):
        self.handle = SliderHandle(self)
        self._pressedPos = QPoint()
        self.lightGrooveColor = QColor()
        self.darkGrooveColor = QColor()
        self.setOrientation(self.orientation())

        self.handle.pressed.connect(self.sliderPressed)
        self.handle.released.connect(self.sliderReleased)
        self.valueChanged.connect(self._adjustHandlePos)

    def setThemeColor(self, light, dark):
        self.lightGrooveColor = QColor(light)
        self.darkGrooveColor = QColor(dark)
        self.handle.setHandleColor(light, dark)
        self.update()

    def setOrientation(self, orientation: Qt.Orientation) -> None:
        super().setOrientation(orientation)
        if orientation == Qt.Orientation.Horizontal:
            self.setMinimumHeight(22)
        else:
            self.setMinimumWidth(22)

    def mousePressEvent(self, e: QMouseEvent):
        self._pressedPos = e.pos()
        self.setValue(self._posToValue(e.pos()))
        self.clicked.emit(self.value())

    def mouseMoveEvent(self, e: QMouseEvent):
        self.setValue(self._posToValue(e.pos()))
        self._pressedPos = e.pos()
        self.sliderMoved.emit(self.value())

    @property
    def grooveLength(self):
        l = (  # noqa
            self.width()
            if self.orientation() == Qt.Orientation.Horizontal
            else self.height()
        )
        return l - self.handle.width()

    def _adjustHandlePos(self):
        total = max(self.maximum() - self.minimum(), 1)
        delta = int((self.value() - self.minimum()) / total * self.grooveLength)

        if self.orientation() == Qt.Orientation.Vertical:
            self.handle.move(0, delta)
        else:
            self.handle.move(delta, 0)

    def _posToValue(self, pos: QPoint):
        pd = self.handle.width() / 2
        gs = max(self.grooveLength, 1)
        v = pos.x() if self.orientation() == Qt.Orientation.Horizontal else pos.y()
        return int((v - pd) / gs * (self.maximum() - self.minimum()) + self.minimum())

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(
            QColor(255, 255, 255, 115) if isDarkTheme() else QColor(0, 0, 0, 100)
        )

        if self.orientation() == Qt.Orientation.Horizontal:
            self._drawHorizonGroove(painter)
            self._drawHorizonTick(painter)
        else:
            self._drawVerticalGroove(painter)
            self._drawVerticalTick(painter)

    def _drawHorizonTick(self, painter: QPainter):
        pass

    def _drawVerticalTick(self, painter: QPainter):
        pass

    def _drawHorizonGroove(self, painter: QPainter):
        w, r = self.width(), self.handle.width() / 2
        painter.drawRoundedRect(QRectF(r, r - 2, w - r * 2, 4), 2, 2)

        if self.maximum() - self.minimum() == 0:
            return

        painter.setBrush(
            autoFallbackThemeColor(self.lightGrooveColor, self.darkGrooveColor)
        )
        aw = (
            (self.value() - self.minimum())
            / (self.maximum() - self.minimum())
            * (w - r * 2)
        )
        painter.drawRoundedRect(QRectF(r, r - 2, aw, 4), 2, 2)

    def _drawVerticalGroove(self, painter: QPainter):
        h, r = self.height(), self.handle.width() / 2
        painter.drawRoundedRect(QRectF(r - 2, r, 4, h - 2 * r), 2, 2)

        if self.maximum() - self.minimum() == 0:
            return

        painter.setBrush(
            autoFallbackThemeColor(self.lightGrooveColor, self.darkGrooveColor)
        )
        ah = (
            (self.value() - self.minimum())
            / (self.maximum() - self.minimum())
            * (h - r * 2)
        )
        painter.drawRoundedRect(QRectF(r - 2, r, 4, ah), 2, 2)

    def resizeEvent(self, e):
        self._adjustHandlePos()


class ClickableSlider(QSlider):
    """A slider can be clicked"""

    clicked = Signal(int)

    def mousePressEvent(self, e: QMouseEvent):
        super().mousePressEvent(e)

        if self.orientation() == Qt.Horizontal:
            value = int(e.pos().x() / self.width() * self.maximum())
        else:
            value = int((self.height() - e.pos().y()) / self.height() * self.maximum())

        self.setValue(value)
        self.clicked.emit(self.value())


class HollowHandleStyle(QProxyStyle):
    """Hollow handle style"""

    def __init__(self, config: dict = None):
        """
        Parameters
        ----------
        config: dict
            style config
        """
        super().__init__()
        self.config = {
            "groove.height": 3,
            "sub-page.color": QColor(255, 255, 255),
            "add-page.color": QColor(255, 255, 255, 64),
            "handle.color": QColor(255, 255, 255),
            "handle.ring-width": 4,
            "handle.hollow-radius": 6,
            "handle.margin": 4,
        }
        config = config if config else {}
        self.config.update(config)

        # get handle size
        w = (
            self.config["handle.margin"]
            + self.config["handle.ring-width"]
            + self.config["handle.hollow-radius"]
        )
        self.config["handle.size"] = QSize(2 * w, 2 * w)

    def subControlRect(
        self,
        cc: QStyle.ComplexControl,
        opt: QStyleOptionSlider,
        sc: QStyle.SubControl,
        widget: QSlider,
    ):
        """get the rectangular area occupied by the sub control"""
        if (
            cc != self.ComplexControl.CC_Slider
            or widget.orientation() != Qt.Horizontal
            or sc == self.SubControl.SC_SliderTickmarks
        ):
            return super().subControlRect(cc, opt, sc, widget)

        rect = widget.rect()

        if sc == self.SubControl.SC_SliderGroove:
            h = self.config["groove.height"]
            grooveRect = QRectF(0, (rect.height() - h) // 2, rect.width(), h)
            return grooveRect.toRect()

        elif sc == self.SubControl.SC_SliderHandle:
            size = self.config["handle.size"]
            x = self.sliderPositionFromValue(
                widget.minimum(), widget.maximum(), widget.value(), rect.width()
            )

            # solve the situation that the handle runs out of slider
            x *= (rect.width() - size.width()) / rect.width()
            sliderRect = QRectF(x, 0, size.width(), size.height())
            return sliderRect.toRect()

    def drawComplexControl(
        self,
        cc: QStyle.ComplexControl,
        opt: QStyleOptionSlider,
        painter: QPainter,
        widget: QSlider,
    ):
        """draw sub control"""
        if cc != self.ComplexControl.CC_Slider or widget.orientation() != Qt.Horizontal:
            return super().drawComplexControl(cc, opt, painter, widget)

        grooveRect = self.subControlRect(
            cc, opt, self.SubControl.SC_SliderGroove, widget
        )
        handleRect = self.subControlRect(
            cc, opt, self.SubControl.SC_SliderHandle, widget
        )
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # paint groove
        painter.save()
        painter.translate(grooveRect.topLeft())

        # paint the crossed part
        w = handleRect.x() - grooveRect.x()
        h = self.config["groove.height"]
        painter.setBrush(self.config["sub-page.color"])
        painter.drawRect(0, 0, w, h)

        # paint the uncrossed part
        x = w + self.config["handle.size"].width()
        painter.setBrush(self.config["add-page.color"])
        painter.drawRect(x, 0, grooveRect.width() - w, h)
        painter.restore()

        # paint handle
        ringWidth = self.config["handle.ring-width"]
        hollowRadius = self.config["handle.hollow-radius"]
        radius = ringWidth + hollowRadius

        path = QPainterPath()
        path.moveTo(0, 0)
        center = handleRect.center() + QPoint(1, 1)
        path.addEllipse(center, radius, radius)
        path.addEllipse(center, hollowRadius, hollowRadius)

        handleColor = self.config["handle.color"]  # type:QColor
        handleColor.setAlpha(
            255 if opt.activeSubControls != self.SubControl.SC_SliderHandle else 153
        )
        painter.setBrush(handleColor)
        painter.drawPath(path)

        # press handle
        if widget.isSliderDown():
            handleColor.setAlpha(255)
            painter.setBrush(handleColor)
            painter.drawEllipse(handleRect)


class ToolTipSlider(Slider):
    """A slider can be clicked

    Constructors
    ------------
    * ToolTipSlider(`parent`: QWidget = None)
    * ToolTipSlider(`orient`: Qt.Orientation, `parent`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(Qt.Horizontal, parent)

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent: QWidget = None):
        super().__init__(orientation, parent)

    def _postInit(self):
        super()._postInit()
        self._toolTip: ToolTip = None
        self._toolTipTimer: QTimer = QTimer(self)
        self._toolTipTimer.setSingleShot(True)
        self._toolTipTimer.timeout.connect(self._hideToolTip)

        self.valueChanged.connect(self._onValueChanged)

    def _onValueChanged(self):
        self._showToolTip()

    def _createToolTip(self):
        tip = ToolTip(str(self.value()), self.window())
        tip.setDuration(-1)
        return tip

    def _showToolTip(self):
        if not self.isVisible():
            return

        if not self._toolTip:
            self._toolTip = self._createToolTip()

        self._toolTip.setText(str(self.value()))
        self._adjustToolTipPos()
        if not self._toolTip.isVisible():
            self._toolTip.show()
        self._toolTipTimer.start(500)

    def _hideToolTip(self):
        if self._toolTip:
            self._toolTip.hide()

    def _adjustToolTipPos(self):
        if not self._toolTip:
            return

        # Position tooltip above the handle
        handlePos = self.handle.mapToGlobal(QPoint(self.handle.width() // 2, 0))
        x = handlePos.x() - self._toolTip.width() // 2
        y = handlePos.y() - self._toolTip.height()

        self._toolTip.move(x, y)

    def enterEvent(self, e):
        self._showToolTip()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._toolTipTimer.start(200)
        super().leaveEvent(e)

    def mousePressEvent(self, e: QMouseEvent):
        self._showToolTip()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._toolTipTimer.start(500)
        super().mouseReleaseEvent(e)


class RangeSlider(QWidget):
    """A slider with two handles for selecting a range

    Constructors
    ------------
    * RangeSlider(`parent`: QWidget = None)
    * RangeSlider(`orient`: Qt.Orientation, `parent`: QWidget = None)
    """

    minValueChanged = Signal(int)
    maxValueChanged = Signal(int)
    rangeChanged = Signal(int, int)

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._postInit(Qt.Horizontal)

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent: QWidget = None):
        super().__init__(parent)
        self._postInit(orientation)

    def _postInit(self, orientation: Qt.Orientation):
        self._orientation = orientation
        self._minimum = 0
        self._maximum = 100
        self._minValue = 0
        self._maxValue = 100
        self._gap = 1  # minimum gap between min and max

        self._pressedPos = QPoint()
        self._pressedHandle = None  # 'min' or 'max'

        self.lightGrooveColor = QColor()
        self.darkGrooveColor = QColor()

        # Create two handles
        self.minHandle = SliderHandle(self)
        self.maxHandle = SliderHandle(self)

        # Create two tooltips
        self._minToolTip: ToolTip = None
        self._maxToolTip: ToolTip = None

        self.__timer = QTimer(self)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self._hideToolTips)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setOrientation(orientation)
        self._connectSignals()

    def _connectSignals(self):
        self.minHandle.pressed.connect(lambda: self._onHandlePressed("min"))
        self.maxHandle.pressed.connect(lambda: self._onHandlePressed("max"))
        self.minHandle.released.connect(self._onHandleReleased)
        self.maxHandle.released.connect(self._onHandleReleased)

    def setOrientation(self, orientation: Qt.Orientation):
        self._orientation = orientation
        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(22)
            self.setMinimumWidth(100)
        else:
            self.setFixedWidth(22)
            self.setMinimumHeight(100)

    def orientation(self) -> Qt.Orientation:
        return self._orientation

    def setMinimum(self, value: int):
        self._minimum = value
        self._minValue = max(self._minValue, value)
        self._maxValue = max(self._maxValue, self._minValue + self._gap)
        self._adjustHandles()

    def minimum(self) -> int:
        return self._minimum

    def setMaximum(self, value: int):
        self._maximum = value
        self._maxValue = min(self._maxValue, value)
        self._minValue = min(self._minValue, self._maxValue - self._gap)
        self._adjustHandles()

    def maximum(self) -> int:
        return self._maximum

    def setRange(self, min_val: int, max_val: int):
        self._minimum = min_val
        self._maximum = max_val
        self._minValue = max(self._minValue, min_val)
        self._maxValue = min(self._maxValue, max_val)
        self._minValue = min(self._minValue, self._maxValue - self._gap)
        self._adjustHandles()

    def setMinValue(self, value: int):
        value = max(self._minimum, min(value, self._maxValue - self._gap))
        if value != self._minValue:
            self._minValue = value
            self._adjustHandles()
            self.minValueChanged.emit(value)
            self.rangeChanged.emit(self._minValue, self._maxValue)

    def minValue(self) -> int:
        return self._minValue

    def setMaxValue(self, value: int):
        value = min(self._maximum, max(value, self._minValue + self._gap))
        if value != self._maxValue:
            self._maxValue = value
            self._adjustHandles()
            self.maxValueChanged.emit(value)
            self.rangeChanged.emit(self._minValue, self._maxValue)

    def maxValue(self) -> int:
        return self._maxValue

    def setValues(self, min_val: int, max_val: int):
        min_val = max(self._minimum, min_val)
        max_val = min(self._maximum, max_val)
        if max_val - min_val < self._gap:
            return
        self._minValue = min_val
        self._maxValue = max_val
        self._adjustHandles()
        self.minValueChanged.emit(self._minValue)
        self.maxValueChanged.emit(self._maxValue)
        self.rangeChanged.emit(self._minValue, self._maxValue)

    def setThemeColor(self, light, dark):
        self.lightGrooveColor = QColor(light)
        self.darkGrooveColor = QColor(dark)
        self.minHandle.setHandleColor(light, dark)
        self.maxHandle.setHandleColor(light, dark)
        self.update()

    @property
    def grooveLength(self):
        l = (  # noqa
            self.width()
            if self._orientation == Qt.Orientation.Horizontal
            else self.height()
        )
        return l - self.minHandle.width()

    def _valueToPos(self, value: int) -> int:
        total = max(self._maximum - self._minimum, 1)
        return int((value - self._minimum) / total * self.grooveLength)

    def _posToValue(self, pos: int) -> int:
        pd = self.minHandle.width() / 2
        gs = max(self.grooveLength, 1)
        return int((pos - pd) / gs * (self._maximum - self._minimum) + self._minimum)

    def _adjustHandles(self):
        minDelta = self._valueToPos(self._minValue)
        maxDelta = self._valueToPos(self._maxValue)

        if self._orientation == Qt.Orientation.Vertical:
            self.minHandle.move(0, minDelta)
            self.maxHandle.move(0, maxDelta)
        else:
            self.minHandle.move(minDelta, 0)
            self.maxHandle.move(maxDelta, 0)

        self.update()

    def _onHandlePressed(self, handle: str):
        self._pressedHandle = handle

    def _onHandleReleased(self):
        self._pressedHandle = None
        self.__timer.start(300)

    def _hideToolTips(self):
        if self._minToolTip:
            self._minToolTip.hide()
        if self._maxToolTip:
            self._maxToolTip.hide()

    def _createToolTip(self, value: str):
        tip = ToolTip(value, self.window())
        tip.setDuration(-1)
        return tip

    def _updateToolTip(self, handle: str):
        """Update tooltip for a single handle."""
        if handle == "min":
            if not self._minToolTip:
                self._minToolTip = self._createToolTip(str(self._minValue))
            tooltip = self._minToolTip
            value = self._minValue
            handleWidget = self.minHandle
        else:
            if not self._maxToolTip:
                self._maxToolTip = self._createToolTip(str(self._maxValue))
            tooltip = self._maxToolTip
            value = self._maxValue
            handleWidget = self.maxHandle

        tooltip.setText(str(value))
        if not tooltip.isVisible():
            tooltip.show()

        # Position tooltip above the handle
        handlePos = handleWidget.mapToGlobal(QPoint(handleWidget.width() // 2, 0))
        x = handlePos.x() - tooltip.width() // 2
        y = handlePos.y() - tooltip.height()
        tooltip.move(x, y)

    def _updateToolTips(self):
        """Update both tooltips (min and max) simultaneously."""
        self._updateToolTip("min")
        self._updateToolTip("max")

    def mousePressEvent(self, e: QMouseEvent):
        self._pressedPos = e.pos()
        # Determine which handle is closer
        if self._orientation == Qt.Orientation.Horizontal:
            pos = e.pos().x()
        else:
            pos = e.pos().y()

        minDist = abs(
            pos - self._valueToPos(self._minValue) - self.minHandle.width() / 2
        )
        maxDist = abs(
            pos - self._valueToPos(self._maxValue) - self.maxHandle.width() / 2
        )

        if minDist < maxDist:
            self._pressedHandle = "min"
        else:
            self._pressedHandle = "max"

        self._updateValue(e.pos())
        self.__timer.stop()

    def mouseMoveEvent(self, e: QMouseEvent):
        self._updateValue(e.pos())

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._pressedHandle = None
        self.__timer.start(300)

    def _updateValue(self, pos: QPoint):
        # keep tooltips visible during dragging
        self.__timer.stop()
        if self._orientation == Qt.Orientation.Horizontal:
            value = self._posToValue(pos.x())
        else:
            value = self._posToValue(pos.y())

        value = max(self._minimum, min(self._maximum, value))

        if self._pressedHandle == "min":
            self.setMinValue(value)
        elif self._pressedHandle == "max":
            self.setMaxValue(value)

        # always show both tooltips while interacting
        self._updateToolTips()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        isDark = isDarkTheme()
        painter.setBrush(QColor(255, 255, 255, 115) if isDark else QColor(0, 0, 0, 100))

        if self._orientation == Qt.Orientation.Horizontal:
            self._drawHorizontalGroove(painter)
        else:
            self._drawVerticalGroove(painter)

    def _drawHorizontalGroove(self, painter: QPainter):
        w, r = self.width(), self.minHandle.width() / 2
        painter.drawRoundedRect(QRectF(r, r - 2, w - r * 2, 4), 2, 2)

        if self._maximum - self._minimum == 0:
            return

        painter.setBrush(
            autoFallbackThemeColor(self.lightGrooveColor, self.darkGrooveColor)
        )

        minPos = self._valueToPos(self._minValue)
        maxPos = self._valueToPos(self._maxValue)
        painter.drawRoundedRect(QRectF(r + minPos, r - 2, maxPos - minPos, 4), 2, 2)

    def _drawVerticalGroove(self, painter: QPainter):
        h, r = self.height(), self.minHandle.width() / 2
        painter.drawRoundedRect(QRectF(r - 2, r, 4, h - 2 * r), 2, 2)

        if self._maximum - self._minimum == 0:
            return

        painter.setBrush(
            autoFallbackThemeColor(self.lightGrooveColor, self.darkGrooveColor)
        )

        minPos = self._valueToPos(self._minValue)
        maxPos = self._valueToPos(self._maxValue)
        painter.drawRoundedRect(QRectF(r - 2, r + minPos, 4, maxPos - minPos), 2, 2)

    def resizeEvent(self, e):
        self._adjustHandles()
