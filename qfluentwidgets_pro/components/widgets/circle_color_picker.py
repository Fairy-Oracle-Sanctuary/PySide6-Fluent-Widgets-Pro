# coding:utf-8
"""A lightweight, single-selection row of customizable circular swatches."""

from operator import index as integerIndex

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QButtonGroup, QHBoxLayout, QSizePolicy, QWidget

from ...common.config import qconfig
from ...common.style_sheet import isDarkTheme


class _CircleColorButton(QAbstractButton):
    """32px hit target, 22px swatch and a 30px selection outline."""

    def __init__(self, color, picker):
        super().__init__(picker)
        self._color = QColor(color)
        self.setCheckable(True)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(self._color.name(QColor.HexArgb if color.alpha() < 255 else QColor.HexRgb))
        # No tooltip: a pointer should reveal only the swatch's hover state.

    def hitButton(self, point):
        return (point.x() - 16) ** 2 + (point.y() - 16) ** 2 <= 16 ** 2

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.update()

    def keyPressEvent(self, event):
        if self.isEnabled() and self.parentWidget()._navigate(self, event.key()):
            event.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.isEnabled():
            self.click()
            event.accept()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(.43)
        circle = QRectF(5, 5, 22, 22)
        if self._color.alpha() < 255:
            # Make transparent custom colors visible without an opaque widget background.
            path = QPainterPath()
            path.addEllipse(circle)
            painter.save()
            painter.setClipPath(path)
            shades = ('#555555', '#777777') if isDarkTheme() else ('#FFFFFF', '#DDDDDD')
            for row in range(6):
                for column in range(6):
                    painter.fillRect(QRectF(5 + column * 4, 5 + row * 4, 4, 4),
                                     QColor(shades[(row + column) % 2]))
            painter.restore()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(circle)
        if self.isEnabled() and (self.underMouse() or self.isDown()):
            shade = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(shade, shade, shade, 30 if self.isDown() else 15))
            painter.drawEllipse(circle)
        painter.setBrush(Qt.NoBrush)
        if self.isChecked():
            color = QColor(self._color)
            color.setAlpha(255)
            painter.setPen(QPen(color, 1.5))
            painter.drawEllipse(QRectF(1, 1, 30, 30))
        elif self.hasFocus():
            painter.setPen(QPen(QColor('#FFFFFF' if isDarkTheme() else '#606060'), 1, Qt.DotLine))
            painter.drawEllipse(QRectF(1, 1, 30, 30))


class CircleColorPicker(QWidget):
    """Pick one color from a horizontal palette; all sizes are logical pixels.

    ``colors`` accepts an iterable of QColor-compatible values. None uses the
    six-color demo palette, while an empty iterable creates an empty picker.
    The first swatch is initially selected. ``setColors`` preserves the current
    color if present, otherwise selects the first swatch (or clears if empty).
    ``setColor`` requires a palette member; ``setCurrentIndex(-1)`` clears the
    selection. Color getters and signals return copies, never owned QColors.
    """

    colorChanged = Signal(QColor)
    currentIndexChanged = Signal(int)

    DEFAULT_COLORS = ('#4BACF2', '#72D6F4', '#4BACF2', '#49A6EB', '#20396C', '#CBB0ED')

    def __init__(self, colors=None, parent=None):
        if isinstance(colors, QWidget) and parent is None:
            parent, colors = colors, None
        super().__init__(parent)
        self._colors = []
        self._currentIndex = -1
        self._buttons = []
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.idClicked.connect(self.setCurrentIndex)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self._layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._layout.addStretch()
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAccessibleName('Color palette')
        qconfig.themeChangedFinished.connect(self._refreshButtons)
        self.setColors(self.DEFAULT_COLORS if colors is None else colors)

    @staticmethod
    def _validatedColors(colors):
        if isinstance(colors, (str, bytes, QColor)):
            raise TypeError('colors must be an iterable of colors, not a single color')
        result = []
        for color in colors:
            try:
                color = QColor(color)
            except (TypeError, ValueError) as error:
                raise ValueError('Invalid palette color') from error
            if not color.isValid():
                raise ValueError('Invalid palette color')
            result.append(color)
        return result

    def colors(self):
        return [QColor(color) for color in self._colors]

    def count(self):
        return len(self._colors)

    def color(self):
        return QColor(self._colors[self._currentIndex]) if self._currentIndex >= 0 else QColor()

    def currentIndex(self):
        return self._currentIndex

    def setColors(self, colors):
        colors = self._validatedColors(colors)  # Atomic validation before any UI changes.
        if colors == self._colors:
            return
        previous, oldIndex = self.color(), self._currentIndex
        hadFocus = any(button.hasFocus() for button in self._buttons)
        for button in self._buttons:
            self._group.removeButton(button)
            self._layout.removeWidget(button)
            button.hide()
            button.deleteLater()
        self._colors, self._buttons = colors, []
        for i, color in enumerate(colors):
            button = _CircleColorButton(color, self)
            self._buttons.append(button)
            self._group.addButton(button, i)
            self._layout.insertWidget(i, button)
        if 0 <= oldIndex < len(colors) and colors[oldIndex] == previous:
            selected = oldIndex
        else:
            selected = colors.index(previous) if previous in colors else (0 if colors else -1)
        self._applySelection(selected)
        if hadFocus and selected >= 0:
            self._buttons[selected].setFocus(Qt.OtherFocusReason)
        self.updateGeometry()
        self._emitChanges(oldIndex, previous)

    def addColors(self, colors):
        self.setColors(self._colors + self._validatedColors(colors))

    def addColor(self, color):
        self.addColors([color])

    def setColor(self, color):
        color = self._validatedColors([color])[0]
        if self.color() == color:
            return
        if color not in self._colors:
            raise ValueError('The selected color must be present in the palette')
        self.setCurrentIndex(self._colors.index(color))

    def setCurrentIndex(self, index):
        if isinstance(index, bool):
            raise TypeError('Palette index must be an integer')
        index = integerIndex(index)
        if not -1 <= index < len(self._colors):
            raise IndexError('Palette index out of range')
        if index == self._currentIndex:
            return
        previous, oldIndex = self.color(), self._currentIndex
        self._applySelection(index)
        self._emitChanges(oldIndex, previous)

    def _applySelection(self, index):
        self._currentIndex = index
        # Temporarily allow clearing an exclusive group's checked button.
        self._group.setExclusive(False)
        for i, button in enumerate(self._buttons):
            button.setChecked(i == index)
        self._group.setExclusive(True)
        self.setAccessibleDescription(self.color().name(QColor.HexArgb) if index >= 0 else 'No color selected')
        self._refreshButtons()

    def _emitChanges(self, oldIndex, previous):
        index, color = self.currentIndex(), self.color()
        if index != oldIndex:
            self.currentIndexChanged.emit(index)
        if color != previous:
            self.colorChanged.emit(color)

    def _refreshButtons(self):
        for button in self._buttons:
            button.update()

    def _navigate(self, button, key):
        index = self._buttons.index(button)
        if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            delta = -1 if key in (Qt.Key_Left, Qt.Key_Up) else 1
            if self.layoutDirection() == Qt.RightToLeft and key in (Qt.Key_Left, Qt.Key_Right):
                delta = -delta
            index = max(0, min(len(self._buttons) - 1, index + delta))
        elif key == Qt.Key_Home:
            index = 0
        elif key == Qt.Key_End:
            index = len(self._buttons) - 1
        else:
            return False
        self.setCurrentIndex(index)
        self._buttons[index].setFocus(Qt.TabFocusReason)
        return True

    def sizeHint(self):
        return QSize(self.count() * 32 + max(0, self.count() - 1) * 10, 32)

    def minimumSizeHint(self):
        return self.sizeHint()
