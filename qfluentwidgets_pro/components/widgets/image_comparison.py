"""Interactive two-image comparison without intermediate scaled bitmaps."""
import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class ImageComparisonSlider(QWidget):
    """Left/right images registered to the same display rectangle.

    setValue() uses a percentage (0..100). Images may be paths, QImage or QPixmap.
    """

    valueChanged = Signal(float)

    def __init__(self, before=None, after=None, parent=None):
        if isinstance(before, QWidget) and after is None and parent is None:
            parent, before = before, None
        super().__init__(parent)
        self._before = QImage()
        self._after = QImage()
        self._value = 50.0
        self._dragging = False
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.SplitHCursor)
        self.setMinimumSize(40, 40)
        self.setImages(before, after)

    @staticmethod
    def _image(image):
        if image is None:
            return QImage()
        if isinstance(image, QPixmap):
            return image.toImage()
        if isinstance(image, QImage):
            return QImage(image)
        return QImage(str(image))

    def setImages(self, before, after):
        self._before, self._after = self._image(before), self._image(after)
        self.updateGeometry()
        self.update()

    def setBeforeImage(self, image):
        self._before = self._image(image)
        self.updateGeometry()
        self.update()

    def setAfterImage(self, image):
        self._after = self._image(image)
        self.updateGeometry()
        self.update()

    def value(self):
        return self._value

    def setValue(self, value):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError('Comparison value must be finite')
        value = max(0.0, min(100.0, value))
        if self._value == value:
            return
        self._value = value
        self.update()
        self.valueChanged.emit(value)

    def sizeHint(self):
        image = self._before if not self._before.isNull() else self._after
        return image.size() if not image.isNull() else QSize(400, 300)

    def scaledToWidth(self, width):
        size = self.sizeHint()
        self.setFixedSize(width, max(1, round(width * size.height() / size.width())))

    def scaledToHeight(self, height):
        size = self.sizeHint()
        self.setFixedSize(max(1, round(height * size.width() / size.height())), height)

    def setScaledSize(self, size):
        self.setFixedSize(size)

    def _moveDivider(self, position):
        if self.width():
            self.setValue(position.x() / self.width() * 100)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self.setFocus(Qt.MouseFocusReason)
            self._moveDivider(event.position())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._moveDivider(event.position())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._moveDivider(event.position())
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def hideEvent(self, event):
        self._dragging = False
        super().hideEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            self.setValue(self._value + (1 if event.key() == Qt.Key_Right else -1))
        elif event.key() == Qt.Key_Home:
            self.setValue(0)
        elif event.key() == Qt.Key_End:
            self.setValue(100)
        else:
            return super().keyPressEvent(event)
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        target = QRectF(self.rect())
        x = self.width() * self._value / 100
        for image, clip in (
            (self._before, QRectF(0, 0, x, self.height())),
            (self._after, QRectF(x, 0, self.width() - x, self.height()))):
            if image.isNull():
                continue
            painter.save()
            painter.setClipRect(clip)
            painter.drawImage(target, image, QRectF(image.rect()))
            painter.restore()
        if self._before.isNull() and self._after.isNull():
            return
        painter.setPen(QPen(QColor(255, 255, 255, 210), 2))
        painter.drawLine(QPointF(x, 0), QPointF(x, self.height()))
        center = self.height() / 2
        handle = QRectF(x - 12, center - 26, 24, 52)
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        painter.setBrush(QColor(255, 255, 255, 185))
        painter.drawRoundedRect(handle, 4, 4)
        painter.setPen(QPen(QColor(0, 0, 0, 210), 1))
        # Stacked opposing arrows, matching the reference's compact grip.
        for y, direction in ((center - 3, 1), (center + 3, -1)):
            painter.drawLine(QPointF(x - 5, y), QPointF(x + 5, y))
            tip = x + 5 * direction
            painter.drawLine(QPointF(tip - 3 * direction, y - 3), QPointF(tip, y))
            painter.drawLine(QPointF(tip - 3 * direction, y + 3), QPointF(tip, y))
