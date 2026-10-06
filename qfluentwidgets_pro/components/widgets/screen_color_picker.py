# coding:utf-8
"""Screen eyedropper using QtGui screenshots, with no optional native dependencies."""

import sys
from math import floor
from weakref import ref

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QSizePolicy, QWidget

from ...common.config import qconfig
from ...common.font import getFont
from ...common.icon import FluentIcon, drawIcon
from ...common.style_sheet import isDarkTheme
from .button import PushButton


def _excludeFromCapture(widget):
    """Exclude only our own live overlays. Load the standard-library bridge lazily."""
    if (sys.platform != 'win32' or QApplication.platformName() != 'windows'
            or sys.getwindowsversion().build < 19041):
        raise RuntimeError('Live screen picking requires Windows 10 version 2004 or newer; '
                           'enable screen freezing on this platform.')
    import ctypes
    from ctypes.wintypes import BOOL, DWORD, HWND

    try:
        affinity = ctypes.WinDLL('user32', use_last_error=True).SetWindowDisplayAffinity
        affinity.argtypes = (HWND, DWORD)
        affinity.restype = BOOL
        if not affinity(HWND(int(widget.winId())), DWORD(0x11)):
            raise RuntimeError('Cannot exclude the live picker overlay from screen capture '
                               '(Windows error %d). Enable screen freezing instead.' % ctypes.get_last_error())
    except (AttributeError, OSError) as error:
        raise RuntimeError('Live screen capture exclusion is unavailable. Enable screen freezing instead.') from error


def _captureLiveColor(screen, geometry, position):
    if screen is None or not _contains(geometry, position):
        return QColor()
    local = QPointF(position) - QPointF(geometry.topLeft())
    x, y = floor(local.x()), floor(local.y())
    # Qt's Windows capture coordinates are screen-local logical pixels. Capture
    # just one logical pixel rather than copying every monitor at 30fps.
    image = screen.grabWindow(0, x, y, 1, 1).toImage()
    if image.isNull():
        raise RuntimeError('Live screen capture failed. Check screen recording permissions.')
    px = min(image.width() - 1, int((local.x() - x) * image.width()))
    py = min(image.height() - 1, int((local.y() - y) * image.height()))
    return image.pixelColor(px, py)


def _drawSwatch(painter, rect, color, radius):
    if color.alpha() < 255:
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.save()
        painter.setClipPath(path)
        shades = ('#555555', '#777777') if isDarkTheme() else ('#FFFFFF', '#DDDDDD')
        for y in range(0, int(rect.height()) + 4, 4):
            for x in range(0, int(rect.width()) + 4, 4):
                painter.fillRect(QRectF(rect.x() + x, rect.y() + y, 4, 4),
                                 QColor(shades[(x // 4 + y // 4) % 2]))
        painter.restore()
    painter.setPen(Qt.NoPen)
    painter.setBrush(color)
    painter.drawRoundedRect(rect, radius, radius)


def _contains(geometry, point):
    return (geometry.x() <= point.x() < geometry.x() + geometry.width()
            and geometry.y() <= point.y() < geometry.y() + geometry.height())


def _sampleImage(image, geometry, globalPos):
    """Map logical global coordinates into this screen's physical screenshot."""
    if image.isNull() or geometry.isEmpty() or not _contains(geometry, globalPos):
        return QColor()
    x = int((globalPos.x() - geometry.x()) * image.width() / geometry.width())
    y = int((globalPos.y() - geometry.y()) * image.height() / geometry.height())
    return image.pixelColor(min(image.width() - 1, x), min(image.height() - 1, y))


def _previewPosition(point, bounds, size):
    x, y = point.x() + 16, point.y() + 16
    if x + size.width() > bounds.x() + bounds.width():
        x = point.x() - size.width() - 16
    if y + size.height() > bounds.y() + bounds.height():
        y = point.y() - size.height() - 16
    return QPoint(max(bounds.x(), min(x, bounds.x() + max(0, bounds.width() - size.width()))),
                  max(bounds.y(), min(y, bounds.y() + max(0, bounds.height() - size.height()))))


class _PreviewCard(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.color = QColor('#FFFFFF')
        self.setFixedSize(106, 40)
        self.setFont(getFont(14))
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 45))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        dark = isDarkTheme()
        border = QColor(255, 255, 255, 20) if dark else QColor(0, 0, 0, 18)
        painter.setPen(QPen(border, 1))
        painter.setBrush(QColor('#2B2B2B' if dark else '#F7F7F7'))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 8, 8)
        swatch = QRectF(4, 4, 32, 32)
        _drawSwatch(painter, swatch, self.color, 4)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(swatch, 4, 4)
        painter.setPen(Qt.white if dark else Qt.black)
        painter.setFont(self.font())
        painter.drawText(QRectF(44, 0, 58, 40), Qt.AlignLeft | Qt.AlignVCenter,
                         self.color.name())


class _ColorPreview(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.card = _PreviewCard(self)
        self.setFixedSize(self.card.width() + 32, self.card.height() + 36)
        self.card.move(16, 12)
        self.hide()

    def setColor(self, color):
        if color != self.card.color:
            self.card.color = QColor(color)
            self.card.update()


class _PickerOverlay(QWidget):
    def __init__(self, picker, screen, geometry, image):
        super().__init__(picker, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._picker = picker
        self._screen = screen
        self._frozen = picker.isFreezeScreenEnabled()
        self._image = image if self._frozen else QImage()
        if not self._frozen:
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.screenGeometry = QRect(geometry)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.ArrowCursor)
        self.setAccessibleName('Screen color picking: click to select, Escape to cancel')
        # Assign each native window to its screen before positioning: mixed DPI
        # desktops cannot be represented by one giant, uniformly scaled window.
        self.winId()
        if screen is not None:
            self.windowHandle().setScreen(screen)
        self.setGeometry(geometry)
        self.preview = _ColorPreview(self)

    def prepare(self):
        if not self._frozen:
            _excludeFromCapture(self)

    def colorAt(self, globalPos):
        if self._frozen:
            return _sampleImage(self._image, self.screenGeometry, globalPos)
        return _captureLiveColor(self._screen, self.screenGeometry, globalPos)

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self._frozen:
            # A zero-alpha layered window passes clicks through on Windows.
            # Minimal alpha retains hit testing while the desktop stays live;
            # capture exclusion removes BOTH this surface and the preview card.
            painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
            return
        # Keep the desktop undimmed. Explicit physical source coordinates avoid
        # implicit devicePixelRatio scaling of the cached screenshot.
        painter.drawImage(QRectF(self.rect()), self._image,
                          QRectF(0, 0, self._image.width(), self._image.height()))

    def mouseMoveEvent(self, event):
        self._picker._previewAt(event.globalPosition())
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._picker._confirmAt(event.globalPosition())
        elif event.button() == Qt.RightButton:
            self._picker.cancelPicking()
        event.accept()

    def mouseReleaseEvent(self, event):
        event.accept()

    def closeEvent(self, event):
        self._picker.cancelPicking()
        event.accept()

    def dispose(self):
        self.hide()
        self._image = QImage()  # Release screenshots now, not at a later event loop turn.
        self.deleteLater()


class ScreenColorPicker(PushButton):
    """Standard PushButton with a swatch and eyedropper; freeze or live sampling.

    ``colorChanged`` reports committed changes (including setColor). ``colorPicked``
    reports every explicit confirmation, even for the same color. ``colorHovered``
    reports preview changes without changing color(). Escape/right-click cancels.
    Screen capture must be permitted by the OS; a null capture emits errorOccurred
    without changing the color. No files, theme color mutations or multimedia imports.
    """

    colorChanged = Signal(QColor)
    colorPicked = Signal(QColor)
    colorHovered = Signal(QColor)
    pickingChanged = Signal(bool)
    pickingCanceled = Signal()
    errorOccurred = Signal(str)

    def __init__(self, color='#0078D4', parent=None):
        if isinstance(color, QWidget) and parent is None:
            parent, color = color, '#0078D4'
        super().__init__(parent=parent)
        self._color = self._validatedColor(color)
        self._freezeScreenEnabled = True
        self._picking = False
        self._overlays = []
        self._screens = []
        self._screenTopologyConnected = False
        self._hoverColor = QColor()
        self._lastPosition = None
        self._previousFocus = None
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._updateFromCursor)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAccessibleName(self.tr('Pick a screen color'))
        self.setAccessibleDescription(self._color.name(QColor.HexArgb))
        self.clicked.connect(self.startPicking)
        qconfig.themeChangedFinished.connect(self._refreshTheme)
        QApplication.instance().aboutToQuit.connect(self.cancelPicking)

    @staticmethod
    def _validatedColor(color):
        try:
            color = QColor(color)
        except (TypeError, ValueError) as error:
            raise ValueError('Invalid screen picker color') from error
        if not color.isValid():
            raise ValueError('Invalid screen picker color')
        return color

    def color(self):
        return QColor(self._color)

    def setColor(self, color):
        color = self._validatedColor(color)
        if color == self._color:
            return
        self._color = color
        self.setAccessibleDescription(color.name(QColor.HexArgb))
        self.update()
        self.colorChanged.emit(QColor(color))

    def isPicking(self):
        return self._picking

    def isFreezeScreenEnabled(self):
        return self._freezeScreenEnabled

    def setFreezeScreenEnabled(self, enabled):
        """Choose frozen (default) or live capture. Changing mode cancels a running session."""
        enabled = bool(enabled)
        if enabled == self._freezeScreenEnabled:
            return
        self.cancelPicking()
        self._freezeScreenEnabled = enabled

    def _captureScreens(self):
        screens = QApplication.screens()
        if not screens:
            raise RuntimeError(self.tr('No screen is available for color picking.'))
        snapshots = []
        for screen in screens:
            image = screen.grabWindow(0).toImage()
            geometry = screen.geometry()
            if image.isNull() or geometry.isEmpty():
                raise RuntimeError(self.tr('Screen capture is unavailable. Check screen recording permissions.'))
            snapshots.append((screen, QRect(geometry), image))
        return snapshots

    def startPicking(self):
        """Return True if started; False if disabled, busy or capture failed."""
        if not self.isEnabled() or self._picking:
            return False
        if any(isinstance(w, _PickerOverlay) and w.isVisible() for w in QApplication.topLevelWidgets()):
            self.errorOccurred.emit(self.tr('Another screen color picker is already active.'))
            return False
        try:
            snapshots = self._captureScreens()  # Capture BEFORE showing any picker UI.
            if not snapshots or any(image.isNull() or geometry.isEmpty() for _, geometry, image in snapshots):
                raise RuntimeError(self.tr('Screen capture is unavailable.'))
        except RuntimeError as error:
            self.errorOccurred.emit(str(error))
            return False
        focus = QApplication.focusWidget()
        self._previousFocus = ref(focus) if focus is not None else None
        self._hoverColor = QColor()
        self._lastPosition = None
        try:
            for screen, geometry, image in snapshots:
                self._overlays.append(_PickerOverlay(self, screen, geometry, image))
            for overlay in self._overlays:
                overlay.prepare()
            self._picking = True
            for overlay in self._overlays:
                overlay.show()
            self._screens = [screen for screen, _, _ in snapshots if screen is not None]
            for screen in self._screens:
                screen.geometryChanged.connect(self.cancelPicking)
                screen.logicalDotsPerInchChanged.connect(self.cancelPicking)
            QApplication.instance().screenRemoved.connect(self.cancelPicking)
            QApplication.instance().screenAdded.connect(self.cancelPicking)
            self._screenTopologyConnected = True
            QApplication.instance().installEventFilter(self)
            active = self._overlayAt(QCursor.pos()) or self._overlays[0]
            active.raise_()
            active.activateWindow()
            active.setFocus(Qt.OtherFocusReason)
        except RuntimeError as error:
            self._cleanup()
            self.errorOccurred.emit(str(error))
            return False
        self.pickingChanged.emit(True)
        if self._picking:
            self._updateFromCursor()
            if self._picking:
                self._timer.start()
        return True

    def _overlayAt(self, position):
        return next((overlay for overlay in self._overlays
                     if _contains(overlay.screenGeometry, position)), None)

    def _updateFromCursor(self):
        if self._picking:
            point = QCursor.pos()
            if self._lastPosition is None or self._lastPosition.toPoint() != point:
                self._previewAt(point)
            elif not self._freezeScreenEnabled:
                self._previewAt(self._lastPosition)

    def _readColor(self, overlay, position):
        try:
            return overlay.colorAt(position)
        except RuntimeError as error:
            self._cleanup()
            self.pickingChanged.emit(False)
            self.errorOccurred.emit(str(error))
            return QColor()

    def _previewAt(self, position):
        if not self._picking or (self._freezeScreenEnabled and position == self._lastPosition):
            return
        self._lastPosition = QPointF(position)
        active = self._overlayAt(position)
        for overlay in self._overlays:
            if overlay is not active:
                overlay.preview.hide()
        if active is None:
            return
        color = self._readColor(active, position)
        if not color.isValid():
            return
        active.preview.setColor(color)
        local = (QPointF(position) - QPointF(active.screenGeometry.topLeft())).toPoint()
        active.preview.move(_previewPosition(local, active.rect(), active.preview.size()))
        active.preview.show()
        if color != self._hoverColor:
            self._hoverColor = QColor(color)
            self.colorHovered.emit(QColor(color))

    def _confirmAt(self, position):
        if not self._picking:
            return
        overlay = self._overlayAt(position)
        color = self._readColor(overlay, position) if overlay else QColor()
        if not color.isValid():
            return
        self._cleanup()
        self.pickingChanged.emit(False)
        self.setColor(color)
        self.colorPicked.emit(QColor(color))

    def cancelPicking(self, *args):
        if not self._picking:
            return
        self._cleanup()
        self.pickingChanged.emit(False)
        self.pickingCanceled.emit()

    def _cleanup(self):
        self._picking = False
        self._timer.stop()
        app = QApplication.instance()
        app.removeEventFilter(self)
        if self._screenTopologyConnected:
            for signal in (app.screenRemoved, app.screenAdded):
                try:
                    signal.disconnect(self.cancelPicking)
                except (RuntimeError, TypeError):
                    pass
            self._screenTopologyConnected = False
        for screen in self._screens:
            try:
                screen.geometryChanged.disconnect(self.cancelPicking)
                screen.logicalDotsPerInchChanged.disconnect(self.cancelPicking)
            except (RuntimeError, TypeError):
                pass
        self._screens = []
        overlays, self._overlays = self._overlays, []
        for overlay in overlays:
            overlay.dispose()
        self._lastPosition = None
        self._hoverColor = QColor()
        focus = self._previousFocus() if self._previousFocus else None
        self._previousFocus = None
        if focus is not None and app.applicationState() == Qt.ApplicationActive:
            try:
                if focus.isVisible() and focus.isEnabled():
                    focus.setFocus(Qt.OtherFocusReason)
            except RuntimeError:
                pass  # The previous widget may have been deleted while picking.

    def eventFilter(self, watched, event):
        if self._picking:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self.cancelPicking()
                    return True
                if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                    self._updateFromCursor()
                    self._confirmAt(self._lastPosition if self._lastPosition is not None else QCursor.pos())
                    return True
            elif event.type() == QEvent.ApplicationDeactivate:
                self.cancelPicking()
        return super().eventFilter(watched, event)

    def _refreshTheme(self):
        self.update()
        for overlay in self._overlays:
            overlay.preview.card.update()

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

    def hideEvent(self, event):
        self.cancelPicking()
        super().hideEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.EnabledChange and not self.isEnabled():
            self.cancelPicking()
        super().changeEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.isEnabled():
            if not event.isAutoRepeat():
                self.click()
            event.accept()
        else:
            super().keyPressEvent(event)

    def sizeHint(self):
        return QSize(60, 32)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        # The inherited button QSS owns background, border and all state styling.
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(.3628)
        elif self.isDown():
            painter.setOpacity(.786)
        x, y = (self.width() - 60) / 2, (self.height() - 32) / 2
        _drawSwatch(painter, QRectF(x + 5, y + 5, 22, 22), self._color, 4)
        drawIcon(FluentIcon.EYEDROPPER, painter, QRectF(x + 36, y + 8, 16, 16))
