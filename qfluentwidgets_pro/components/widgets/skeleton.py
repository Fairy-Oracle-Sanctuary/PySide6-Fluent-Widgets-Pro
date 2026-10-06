"""Lightweight, native loading placeholders with a clipped shimmer sweep."""

from math import cos, isfinite, pi, sin, tan

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QRectF, QSize, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import QSizePolicy, QWidget

from ...common.config import qconfig
from ...common.style_sheet import isDarkTheme


class SkeletonWidget(QWidget):
    """A transparent canvas for caller-defined rounded rectangles and ellipses.

    All shapes share one left-to-right shimmer, not one animation per shape.
    Absolute geometry uses logical pixels; relative geometry uses fractions of
    the current widget size. No widgets, images or text are read from content.
    Subclasses may override skeletonPath() for their own responsive layouts.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shapes = []
        self._phase = 0.
        self._animationEnabled = True
        self._baseColors = (QColor('#e5e5e5'), QColor('#3d3d3d'))
        self._highlightColors = (QColor(255, 255, 255, 220), QColor(255, 255, 255, 80))
        self._animation = QVariantAnimation(self)
        self._animation.setStartValue(0.)
        self._animation.setEndValue(1.)
        self._animation.setDuration(1500)
        self._animation.setLoopCount(-1)
        self._animation.setEasingCurve(QEasingCurve.Linear)
        self._animation.valueChanged.connect(self._setPhase)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAccessibleName(self.tr('Loading'))
        qconfig.themeChangedFinished.connect(self.update)

    def sizeHint(self):
        return QSize(520, 100)

    def minimumSizeHint(self):
        return QSize(0, self.sizeHint().height())

    @staticmethod
    def _rect(rect):
        rect = QRectF(rect)
        if (not all(isfinite(v) for v in (rect.x(), rect.y(), rect.width(), rect.height()))
                or rect.width() <= 0 or rect.height() <= 0):
            raise ValueError('Skeleton geometry must be finite with positive dimensions')
        return rect

    def addRect(self, rect, radius=6, relative=False):
        """Add a rounded rectangle; radius is always in logical pixels."""
        rect = self._rect(rect)
        radius = float(radius)
        if not isfinite(radius) or radius < 0:
            raise ValueError('Skeleton corner radius must be finite and nonnegative')
        self._shapes.append((rect, radius, False, bool(relative)))
        self.update()

    def addEllipse(self, rect, relative=False):
        """Add an ellipse (a circle when rect has equal width and height)."""
        self._shapes.append((self._rect(rect), 0., True, bool(relative)))
        self.update()

    def clear(self):
        """Remove caller-defined shapes, without changing animation settings."""
        self._shapes.clear()
        self.update()

    def skeletonPath(self):
        """Return a fresh path; callers may override this instead of adding shapes."""
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        for rect, radius, ellipse, relative in self._shapes:
            if relative:
                rect = QRectF(rect.x() * self.width(), rect.y() * self.height(),
                              rect.width() * self.width(), rect.height() * self.height())
            if ellipse:
                path.addEllipse(rect)
            else:
                r = min(radius, rect.width() / 2, rect.height() / 2)
                path.addRoundedRect(rect, r, r)
        return path

    def baseColor(self):
        return QColor(self._baseColors[int(isDarkTheme())])

    def highlightColor(self):
        return QColor(self._highlightColors[int(isDarkTheme())])

    def setColors(self, baseLight, baseDark, highlightLight=None, highlightDark=None):
        """Set neutral fill and optional alpha-aware shimmer colors for both themes."""
        base = tuple(QColor(c) for c in (baseLight, baseDark))
        highlight = tuple(QColor(c) if c is not None else QColor(previous)
                          for c, previous in zip((highlightLight, highlightDark), self._highlightColors))
        if not all(c.isValid() for c in base + highlight):
            raise ValueError('Invalid skeleton color')
        self._baseColors, self._highlightColors = base, highlight
        self.update()

    def isAnimationEnabled(self):
        return self._animationEnabled

    def setAnimationEnabled(self, enabled):
        """False shows static placeholders; True animates while visible."""
        self._animationEnabled = bool(enabled)
        if not self._animationEnabled:
            self._animation.stop()
            self._phase = 0.
        elif self.isVisible():
            self._startAnimation()
        self.update()

    def animationDuration(self):
        return self._animation.duration()

    def setAnimationDuration(self, duration):
        duration = int(duration)
        if duration <= 0:
            raise ValueError('Skeleton animation duration must be positive')
        self._animation.setDuration(duration)

    def _setPhase(self, phase):
        self._phase = float(phase)
        self.update()

    def _startAnimation(self):
        if self._animation.state() == QAbstractAnimation.Paused:
            self._animation.resume()
        elif self._animation.state() == QAbstractAnimation.Stopped:
            self._animation.start()

    def showEvent(self, event):
        super().showEvent(event)
        if self._animationEnabled:
            self._startAnimation()

    def hideEvent(self, event):
        if self._animation.state() == QAbstractAnimation.Running:
            self._animation.pause()
        super().hideEvent(event)

    def _shimmerGradient(self):
        # Rotate the vertical band clockwise by 30 degrees. Its normal points
        # down/right in Qt's screen coordinates; lower rows peak further left.
        angle = pi / 6
        band = max(40., self.width() * .3)
        margin = band + self.height() * tan(angle) / 2
        center = -margin + self._phase * (self.width() + 2 * margin)
        dx, dy = band * cos(angle) / 2, band * sin(angle) / 2
        y = self.height() / 2
        gradient = QLinearGradient(center - dx, y - dy, center + dx, y + dy)
        highlight = self.highlightColor()
        transparent = QColor(highlight)
        transparent.setAlpha(0)
        gradient.setColorAt(0., transparent)
        gradient.setColorAt(.5, highlight)
        gradient.setColorAt(1., transparent)
        return gradient

    def paintEvent(self, event):
        path = self.skeletonPath()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(.43)
        painter.fillPath(path, self.baseColor())
        if self._animationEnabled and not path.isEmpty():
            # Only the placeholders receive the highlight; gaps stay transparent.
            painter.fillPath(path, self._shimmerGradient())


class _PersonalInfoSkeleton(SkeletonWidget):
    _roundAvatar = False

    def skeletonPath(self):
        path = super().skeletonPath()
        # Preserve reference proportions at normal widths, shrink without overflow.
        avatar = min(100., self.height(), max(0., self.width() / 4))
        left = avatar + min(20., max(0., self.width() - avatar))
        width = max(0., min(400., self.width() - left))
        rect = QRectF(0, (self.height() - avatar) / 2, avatar, avatar)
        if self._roundAvatar:
            path.addEllipse(rect)
        else:
            path.addRoundedRect(rect, 6, 6)
        y = (self.height() - 100) / 2
        path.addRoundedRect(QRectF(left, y + 10, width, 30), 6, 6)
        path.addRoundedRect(QRectF(left, y + 60, width / 2, 30), 6, 6)
        return path


class CirclePersonalInfoSkeleton(_PersonalInfoSkeleton):
    """A 100-pixel circular avatar with a long and a short text placeholder."""
    _roundAvatar = True


class RectanglePersonalInfoSkeleton(_PersonalInfoSkeleton):
    """A rounded square avatar with a long and a short text placeholder."""


class ArticleSkeleton(SkeletonWidget):
    """A 112-pixel article image with four alternating long/short text lines."""

    def sizeHint(self):
        return QSize(544, 112)

    def skeletonPath(self):
        path = super().skeletonPath()
        image = min(112., self.height(), max(0., self.width() / 4))
        left = image + min(20., max(0., self.width() - image))
        width = max(0., min(412., self.width() - left))
        y = (self.height() - 112) / 2
        path.addRoundedRect(QRectF(0, (self.height() - image) / 2, image, image), 4, 4)
        for top, ratio in ((4, 1.), (28, .55), (64, 1.), (90, .55)):
            path.addRoundedRect(QRectF(left, y + top, width * ratio, 18), 4, 4)
        return path
