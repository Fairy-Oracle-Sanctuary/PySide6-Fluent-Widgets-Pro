"""Native, mouse-transparent tiled text watermarks for QWidget content."""

from math import ceil, cos, isfinite, pi, sin

from PySide6.QtCore import QEvent, QRectF, QSize, QSizeF, Qt, QTimer
from PySide6.QtGui import QColor, QFontMetricsF, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from ...common.config import qconfig
from ...common.font import getFont
from ...common.style_sheet import isDarkTheme


class Watermark(QWidget):
    """A transparent text overlay, automatically fitted to its target widget.

    ``Watermark(text, target)`` attaches and shows the overlay without adding it
    to a layout. Mouse, wheel and keyboard interaction stays with real content.
    Caller-provided text is literal, never translated or interpreted as HTML.
    This is a visual label, not copy protection or an image/PDF export engine.
    """

    def __init__(self, text='', parent=None):
        super().__init__()
        self._target = None
        self._text = str(text)
        self._angle = -15.
        self._opacity = .1
        self._spacing = QSizeF(60, 30)
        self._colors = (QColor(Qt.black), QColor(Qt.white))
        self._tile = None
        self._tileDpr = None
        self._syncTimer = QTimer(self)
        self._syncTimer.setSingleShot(True)
        self._syncTimer.timeout.connect(self._syncTarget)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFont(getFont(18))
        qconfig.themeChangedFinished.connect(self._invalidateTile)
        if parent is not None:
            self.setTargetWidget(parent)

    def sizeHint(self):
        return QSize(640, 240)

    def targetWidget(self):
        return self._target

    def setTargetWidget(self, target):
        """Attach/retarget; None detaches and hides without opening a window.

        For scroll views attach to viewport() to keep the watermark stationary.
        Explicitly hidden overlays remain hidden when retargeted.
        """
        if target is not None and not isinstance(target, QWidget):
            raise TypeError('Watermark target must be a QWidget or None')
        if target is self or (target is not None and self.isAncestorOf(target)):
            raise ValueError('Watermark cannot target itself or its descendants')
        if target is self._target:
            return
        visible = self._target is None or not self.isHidden()
        if self._target is not None:
            self._target.removeEventFilter(self)
            for child in self._target.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
                child.removeEventFilter(self)
        self._syncTimer.stop()
        self.hide()
        self._target = target
        self.setParent(target)
        if target is not None:
            target.installEventFilter(self)
            self._syncTarget()
            self.setVisible(visible)

    def _syncTarget(self):
        if self._target is None:
            return
        self.setGeometry(self._target.rect())
        # Track direct siblings as well as new children. A late show()/raise_()
        # must not silently bury the watermark behind newly inserted content.
        for child in self._target.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            if child is not self:
                child.installEventFilter(self)
        self.raise_()

    def eventFilter(self, watched, event):
        kind = event.type()
        if watched is self._target:
            if kind in (QEvent.Resize, QEvent.Show):
                self._syncTarget()
            elif kind in (QEvent.ChildAdded, QEvent.ChildPolished, QEvent.ChildRemoved):
                # ChildAdded can fire before a QWidget constructor finishes.
                self._syncTimer.start()
        elif isinstance(watched, QWidget):
            if kind == QEvent.ParentChange and watched.parentWidget() is not self._target:
                watched.removeEventFilter(self)
            elif watched.parentWidget() is self._target and kind in (QEvent.ZOrderChange, QEvent.Show):
                self._syncTimer.start()
        return super().eventFilter(watched, event)

    def text(self):
        return self._text

    def setText(self, text):
        text = str(text)
        if text != self._text:
            self._text = text
            self._invalidateTile()

    @staticmethod
    def _number(value, label):
        value = float(value)
        if not isfinite(value):
            raise ValueError(label + ' must be finite')
        return value

    def angle(self):
        return self._angle

    def setAngle(self, angle):
        """Degrees; positive is clockwise, negative is counterclockwise."""
        angle = self._number(angle, 'Watermark angle')
        self._angle = (angle + 180) % 360 - 180
        self._invalidateTile()

    def opacity(self):
        return self._opacity

    def setOpacity(self, opacity):
        opacity = self._number(opacity, 'Watermark opacity')
        if not 0 <= opacity <= 1:
            raise ValueError('Watermark opacity must be between zero and one')
        self._opacity = opacity
        self.update()

    def spacing(self):
        return QSizeF(self._spacing)

    def setSpacing(self, horizontal, vertical=None):
        """Gaps between rotated text tiles, in logical pixels (not center steps)."""
        horizontal = self._number(horizontal, 'Horizontal watermark spacing')
        vertical = horizontal if vertical is None else self._number(vertical, 'Vertical watermark spacing')
        if horizontal < 0 or vertical < 0:
            raise ValueError('Watermark spacing must be nonnegative')
        self._spacing = QSizeF(horizontal, vertical)
        self._invalidateTile()

    def color(self):
        return QColor(self._colors[int(isDarkTheme())])

    def setColor(self, light, dark=None):
        """Set colors for both themes; a single color applies to either theme."""
        colors = (QColor(light), QColor(light if dark is None else dark))
        if not all(color.isValid() for color in colors):
            raise ValueError('Invalid watermark color')
        self._colors = colors
        self._invalidateTile()

    def _invalidateTile(self):
        self._tile = None
        self.update()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.FontChange:
            self._invalidateTile()

    def _createTile(self):
        metrics = QFontMetricsF(self.font())
        lines = self._text.split('\n')
        width = max(max(metrics.horizontalAdvance(line), metrics.boundingRect(line).width())
                    for line in lines) + 4
        height = metrics.height() * len(lines) + 4
        radians = self._angle * pi / 180
        c, s = abs(cos(radians)), abs(sin(radians))
        tileWidth = max(1, ceil(width * c + height * s + self._spacing.width()))
        tileHeight = max(1, ceil(width * s + height * c + self._spacing.height()))
        dpr = self.devicePixelRatioF()
        tile = QPixmap(ceil(tileWidth * dpr), ceil(tileHeight * dpr))
        tile.setDevicePixelRatio(dpr)
        tile.fill(Qt.transparent)
        if not tile.isNull():
            painter = QPainter(tile)
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
            painter.setFont(self.font())
            painter.setPen(self.color())
            painter.translate(tileWidth / 2, tileHeight / 2)
            painter.rotate(self._angle)
            painter.drawText(QRectF(-width / 2, -height / 2, width, height), Qt.AlignCenter, self._text)
            painter.end()
        self._tile, self._tileDpr = tile, dpr

    def paintEvent(self, event):
        if not self._text or self._opacity == 0:
            return
        if self._tile is None or self._tileDpr != self.devicePixelRatioF():
            self._createTile()
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        # One cached, DPR-aware tile and one native call, even for large windows.
        painter.drawTiledPixmap(self.rect(), self._tile)
