"""Image label with a cursor-following circular magnifying lens."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPen

from ...common.config import qconfig
from ...common.style_sheet import themeColor
from .label import ImageLabel


class ImageMagnifierWidget(ImageLabel):
    """ImageLabel APIs plus a theme-colored, local-detail magnifying lens.

    Magnification is relative to the displayed image. Source pixels are sampled
    directly, rather than enlarging a previously downscaled preview.
    """

    def _postInit(self):
        super()._postInit()
        self._magnification = 2.0
        self._radius = 50
        self._magnifierEnabled = True
        self._hovering = False
        self._position = QPointF()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        qconfig.themeColorChanged.connect(self.update)
        qconfig.themeChangedFinished.connect(self.update)

    def setMagnification(self, factor):
        factor = float(factor)
        if not math.isfinite(factor) or factor < 1:
            raise ValueError('Magnification must be finite and at least 1')
        self._magnification = factor
        self.update()

    def magnification(self):
        return self._magnification

    def setRadius(self, radius):
        self._radius = max(8, int(radius))
        self.update()

    def radius(self):
        return self._radius

    def setMagnifierEnabled(self, enabled):
        self._magnifierEnabled = bool(enabled)
        self.update()

    def isMagnifierEnabled(self):
        return self._magnifierEnabled

    def enterEvent(self, event):
        self._hovering = True
        self._position = event.position()
        self.update()
        super().enterEvent(event)

    def mouseMoveEvent(self, event):
        self._position = event.position()
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hovering = False
        self.update()
        super().leaveEvent(event)

    def focusInEvent(self, event):
        if not self._hovering:
            self._position = QPointF(self.width() / 2, self.height() / 2)
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.update()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        moves = {Qt.Key_Left: (-5, 0), Qt.Key_Right: (5, 0),
                 Qt.Key_Up: (0, -5), Qt.Key_Down: (0, 5)}
        if event.key() in moves and self._magnifierEnabled:
            dx, dy = moves[event.key()]
            self._position = QPointF(
                max(0, min(self.width(), self._position.x() + dx)),
                max(0, min(self.height(), self._position.y() + dy)))
            self.update()
            event.accept()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if (self.isNull() or not self._magnifierEnabled or not self.isEnabled()
                or not (self._hovering or self.hasFocus())
                or self.width() <= 0 or self.height() <= 0):
            return
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        x, y = self._position.x(), self._position.y()
        radius = self._radius
        lens = QRectF(x - radius, y - radius, radius * 2, radius * 2)
        path = QPainterPath()
        path.addEllipse(lens)
        painter.save()
        painter.setClipPath(path)
        # Transform the original image around the cursor; this also handles
        # non-uniform ImageLabel.setScaledSize() and high-DPI source images.
        factor = self._magnification
        target = QRectF(x * (1 - factor), y * (1 - factor),
                        self.width() * factor, self.height() * factor)
        painter.drawImage(target, self.image, QRectF(self.image.rect()))
        painter.restore()
        color = themeColor()
        painter.setPen(QPen(color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(lens.adjusted(1.5, 1.5, -1.5, -1.5))
        painter.setPen(QPen(color, 0.5))
        painter.drawLine(QPointF(x - 12, y), QPointF(x + 12, y))
        painter.drawLine(QPointF(x, y - 12), QPointF(x, y + 12))
