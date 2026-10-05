# coding:utf-8
"""Numeric rating display with a single vector star."""

from math import cos, isfinite, pi, sin

from PySide6.QtCore import QEvent, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ...common.config import qconfig
from ...common.font import getFont
from ...common.style_sheet import isDarkTheme


def _starPath(cx, cy, radius=8):
    path = QPainterPath()
    for i in range(10):
        angle = -pi / 2 + i * pi / 5
        r = radius if i % 2 == 0 else radius * .475
        x, y = cx + r * cos(angle), cy + r * sin(angle)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.closeSubpath()
    return path


class RatingWidget(QWidget):
    """Display a caller-provided rating, not an interactive five-star selector.

    Scores may use any finite numeric scale. Display precision defaults to one
    decimal place; redundant trailing zeros are omitted.
    """

    valueChanged = Signal(float)

    def __init__(self, value=0, parent=None):
        super().__init__(parent)
        self._value = self._validateValue(value)
        self._decimals = 1
        self._lightStarColor = QColor("#F88A00")
        self._darkStarColor = QColor("#F88A00")
        self.setFont(getFont(20, QFont.DemiBold))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAccessibleName("Rating")
        self.setAccessibleDescription(self.text())
        qconfig.themeChangedFinished.connect(self.update)

    @staticmethod
    def _validateValue(value):
        value = float(value)
        if not isfinite(value):
            raise ValueError("RatingWidget requires a finite score")
        return value

    def value(self):
        return self._value

    def setValue(self, value):
        value = self._validateValue(value)
        if value == self._value:
            return
        self._value = value
        self._refresh()
        self.valueChanged.emit(value)

    def decimals(self):
        return self._decimals

    def setDecimals(self, decimals):
        decimals = int(decimals)
        if not 0 <= decimals <= 6:
            raise ValueError("Display precision must be between 0 and 6")
        self._decimals = decimals
        self._refresh()

    def text(self):
        text = f"{self._value:.{self._decimals}f}"
        if self._decimals:
            text = text.rstrip("0").rstrip(".")
        return "0" if text == "-0" else text

    def _refresh(self):
        self.setAccessibleDescription(self.text())
        self.updateGeometry()
        self.update()

    def setStarColor(self, light, dark=None):
        light, dark = QColor(light), QColor(light if dark is None else dark)
        if not light.isValid() or not dark.isValid():
            raise ValueError("Invalid star color")
        self._lightStarColor, self._darkStarColor = light, dark
        self.update()

    def starColor(self):
        return QColor(self._darkStarColor if isDarkTheme() else self._lightStarColor)

    def sizeHint(self):
        return QSize(self.fontMetrics().horizontalAdvance(self.text()) + 24,
                     max(24, self.fontMetrics().height()))

    def minimumSizeHint(self):
        return self.sizeHint()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.FontChange:
            self.updateGeometry()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        painter.setFont(self.font())
        if not self.isEnabled():
            painter.setOpacity(.43)
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        textWidth = self.fontMetrics().horizontalAdvance(self.text())
        painter.drawText(QRectF(0, 0, textWidth, self.height()),
                         Qt.AlignLeft | Qt.AlignVCenter, self.text())
        # A vector star stays crisp at fractional/high DPI scaling.
        cx, cy = textWidth + 14, self.height() / 2
        star = _starPath(cx, cy)
        color = self.starColor()
        painter.setPen(QPen(color, 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(color)
        painter.drawPath(star)


class InteractiveRatingWidget(RatingWidget):
    """Five continuous-fill stars: hover previews, click commits, leave restores.

    Mouse coordinates are not rounded to integer or half-star ratings. The gap
    after a star keeps that star fully filled without advancing the next one.
    """

    hovered = Signal(float)
    _starSize = 20
    _spacing = 4
    _count = 5

    def __init__(self, value=0, parent=None):
        self._hoverValue = None
        self._readOnly = False
        self._pressed = False
        super().__init__(max(0, min(5, self._validateValue(value))), parent)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def sizeHint(self):
        return QSize(self._count * self._starSize + (self._count - 1) * self._spacing, 24)

    def setValue(self, value):
        value = max(0, min(self._count, self._validateValue(value)))
        self._hoverValue = None
        super().setValue(value)
        self.update()

    def displayValue(self):
        return self._value if self._hoverValue is None else self._hoverValue

    def isReadOnly(self):
        return self._readOnly

    def setReadOnly(self, enabled):
        self._readOnly = bool(enabled)
        self._pressed = False
        self._clearPreview()
        self.setCursor(Qt.ArrowCursor if self._readOnly else Qt.PointingHandCursor)

    def _valueAt(self, x):
        x = max(0., min(float(self.sizeHint().width()), float(x)))
        stride = self._starSize + self._spacing
        index = int(x // stride)
        return min(float(self._count), index + min(1., (x - index * stride) / self._starSize))

    def _fillPosition(self, value):
        whole = int(value)
        if whole >= self._count:
            return float(self.sizeHint().width())
        return whole * (self._starSize + self._spacing) + (value - whole) * self._starSize

    def _preview(self, x):
        value = self._valueAt(x)
        if value == self._hoverValue:
            return
        self._hoverValue = value
        self.update()
        self.hovered.emit(value)

    def _clearPreview(self):
        if self._hoverValue is not None:
            self._hoverValue = None
            self.update()
            self.hovered.emit(self._value)

    def mouseMoveEvent(self, event):
        if self.isEnabled() and not self._readOnly:
            self._preview(event.position().x())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._clearPreview()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled() and not self._readOnly:
            self._pressed = True
            self.setFocus(Qt.MouseFocusReason)
            self._preview(event.position().x())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            if self.isEnabled() and not self._readOnly and self.rect().contains(event.position().toPoint()):
                self.setValue(self._valueAt(event.position().x()))
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.isEnabled() and not self._readOnly:
            if event.key() in (Qt.Key_Left, Qt.Key_Down, Qt.Key_Right, Qt.Key_Up):
                delta = -.1 if event.key() in (Qt.Key_Left, Qt.Key_Down) else .1
                self.setValue(self.value() + delta)
            elif event.key() == Qt.Key_Home:
                self.setValue(0)
            elif event.key() == Qt.Key_End:
                self.setValue(self._count)
            else:
                return super().keyPressEvent(event)
            event.accept()
        else:
            super().keyPressEvent(event)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.EnabledChange and not self.isEnabled():
            self._pressed = False
            self._clearPreview()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(.43)
        color = self.starColor()
        paths = [_starPath(i * (self._starSize + self._spacing) + self._starSize / 2,
                           self.height() / 2) for i in range(self._count)]
        painter.save()
        painter.setClipRect(QRectF(0, 0, self._fillPosition(self.displayValue()), self.height()))
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        for path in paths:
            painter.drawPath(path)
        painter.restore()
        painter.setPen(QPen(color, 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        for path in paths:
            painter.drawPath(path)
        if self.hasFocus():
            painter.setPen(QPen(color, 1, Qt.DotLine))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 3, 3)
