"""Reusable, parent-scoped native drawers with a sliding panel and shadow."""

from enum import Enum

from PySide6.QtCore import QEasingCurve, QEvent, QRect, QSize, Qt, QTimer, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QHBoxLayout, QLayout, QVBoxLayout, QWidget

from ...common.config import qconfig
from ...common.icon import FluentIcon
from ...common.style_sheet import isDarkTheme
from .button import TransparentToolButton
from .label import SubtitleLabel


class DrawerPosition(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    TOP = 'top'
    BOTTOM = 'bottom'


class _DrawerPanel(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#202020' if isDarkTheme() else '#ffffff'))


class Drawer(QWidget):
    """Slide custom content over a parent QWidget, without opening another window.

    ``open()``/``show()`` animate in, ``close()`` animates out, ``hide()`` hides
    immediately. The object and caller-provided content are reusable. Parent
    resize updates geometry even during animation; parent hide dismisses it.
    Attach to the content area to leave a frameless window's title bar uncovered.
    """

    opened = Signal()
    closed = Signal()

    def __init__(self, title='', parent=None, position=DrawerPosition.RIGHT):
        if not isinstance(parent, QWidget):
            raise ValueError('Drawer requires a parent QWidget')
        super().__init__(parent)
        self._position = DrawerPosition(position)
        self._drawerSize = 320
        self._duration = 240
        self._progress = 0.
        self._open = False
        self._previousFocus = None
        self._maskColor = QColor(0, 0, 0, 45)
        self._maskClosable = True
        self._animation = QVariantAnimation(self)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.valueChanged.connect(self._setProgress)
        self._animation.finished.connect(self._animationFinished)
        self._raiseTimer = QTimer(self)
        self._raiseTimer.setSingleShot(True)
        self._raiseTimer.timeout.connect(self._raiseIfVisible)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.panel = _DrawerPanel(self)
        self.shadowEffect = QGraphicsDropShadowEffect(self.panel)
        self.shadowEffect.setBlurRadius(48)
        self.shadowEffect.setOffset(0, 0)
        self.shadowEffect.setColor(QColor(0, 0, 0, 110))
        self.panel.setGraphicsEffect(self.shadowEffect)
        panelLayout = QVBoxLayout(self.panel)
        panelLayout.setSizeConstraint(QLayout.SetNoConstraint)
        panelLayout.setContentsMargins(0, 0, 0, 0)
        panelLayout.setSpacing(0)
        self.headerWidget = QWidget(self.panel)
        header = QHBoxLayout(self.headerWidget)
        header.setContentsMargins(20, 16, 12, 8)
        self.titleLabel = SubtitleLabel(str(title), self.headerWidget)
        self.titleLabel.setTextFormat(Qt.PlainText)
        self.titleLabel.setVisible(bool(title))
        header.addWidget(self.titleLabel, 1)
        self.closeButton = TransparentToolButton(FluentIcon.CLOSE, self.headerWidget)
        self.closeButton.setFixedSize(32, 32)
        self.closeButton.setIconSize(QSize(16, 16))
        self.closeButton.setToolTip(self.tr('Close'))
        self.closeButton.setAccessibleName(self.tr('Close'))
        self.closeButton.clicked.connect(self.close)
        header.addWidget(self.closeButton, 0, Qt.AlignTop)
        self.contentWidget = QWidget(self.panel)
        self.viewLayout = QVBoxLayout(self.contentWidget)
        self.viewLayout.setContentsMargins(20, 12, 20, 20)
        self.viewLayout.setSpacing(12)
        panelLayout.addWidget(self.headerWidget)
        panelLayout.addWidget(self.contentWidget, 1)
        self._escape = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._escape.setContext(Qt.WidgetWithChildrenShortcut)
        self._escape.activated.connect(self.close)
        parent.installEventFilter(self)
        qconfig.themeChangedFinished.connect(self._applyTheme)
        self.setGeometry(parent.rect())
        QWidget.hide(self)
        self._updatePanelGeometry()

    def title(self):
        return self.titleLabel.text()

    def setTitle(self, title):
        self.titleLabel.setText(str(title))
        self.titleLabel.setVisible(bool(title))

    def addWidget(self, widget, stretch=0, alignment=Qt.Alignment()):
        """Add arbitrary content; layouts can also be inserted into viewLayout."""
        if not isinstance(widget, QWidget):
            raise TypeError('Drawer content must be a QWidget')
        if widget is self or widget.isAncestorOf(self.contentWidget):
            raise ValueError('Drawer cannot contain itself or its ancestors')
        self.viewLayout.addWidget(widget, stretch, alignment)

    def position(self):
        return self._position

    def setPosition(self, position):
        self._position = DrawerPosition(position)
        self._updatePanelGeometry()

    def drawerSize(self):
        return self._drawerSize

    def setDrawerSize(self, size):
        """Width for left/right, height for top/bottom, in logical pixels."""
        size = int(size)
        if size <= 0:
            raise ValueError('Drawer size must be positive')
        self._drawerSize = size
        self._updatePanelGeometry()

    def animationDuration(self):
        return self._duration

    def setAnimationDuration(self, duration):
        duration = int(duration)
        if duration < 0:
            raise ValueError('Drawer animation duration must be nonnegative')
        self._duration = duration

    def maskColor(self):
        return QColor(self._maskColor)

    def setMaskColor(self, color):
        color = QColor(color)
        if not color.isValid():
            raise ValueError('Invalid drawer mask color')
        self._maskColor = color
        self.update()

    def isClosableOnMaskClicked(self):
        return self._maskClosable

    def setClosableOnMaskClicked(self, enabled):
        self._maskClosable = bool(enabled)

    def setEscClosable(self, enabled):
        self._escape.setEnabled(bool(enabled))

    def isEscClosable(self):
        return self._escape.isEnabled()

    def isOpen(self):
        """True while opening/open; False once dismissal starts."""
        return self._open

    def open(self, position=None):
        if position is not None:
            self.setPosition(position)
        if self._open and self.isVisible():
            self.raise_()
            return
        if self.isHidden():
            self._previousFocus = QApplication.focusWidget()
        self._open = True
        self.setGeometry(self.parentWidget().rect())
        QWidget.show(self)
        self.raise_()
        self.setFocus(Qt.PopupFocusReason)
        self._animateTo(1.)

    def show(self):
        self.open()

    def close(self):
        if not self._open:
            return True
        self._open = False
        self._animateTo(0.)
        return True

    def hide(self):
        self._finishClosed()

    def _animateTo(self, destination):
        self._animation.stop()
        duration = round(self._duration * abs(destination - self._progress))
        if duration == 0:
            self._setProgress(destination)
            self._animationFinished()
            return
        self._animation.setStartValue(self._progress)
        self._animation.setEndValue(destination)
        self._animation.setDuration(duration)
        self._animation.start()

    def _setProgress(self, value):
        self._progress = float(value)
        self._updatePanelGeometry()
        self.update()

    def _updatePanelGeometry(self):
        w, h, p = self.width(), self.height(), self._progress
        vertical = self._position in (DrawerPosition.LEFT, DrawerPosition.RIGHT)
        extent = min(self._drawerSize, w if vertical else h)
        if self._position == DrawerPosition.LEFT:
            rect = QRect(round(-extent * (1 - p)), 0, extent, h)
        elif self._position == DrawerPosition.RIGHT:
            rect = QRect(round(w - extent * p), 0, extent, h)
        elif self._position == DrawerPosition.TOP:
            rect = QRect(0, round(-extent * (1 - p)), w, extent)
        else:
            rect = QRect(0, round(h - extent * p), w, extent)
        self.panel.setGeometry(rect)

    def _animationFinished(self):
        if self._open:
            self._setProgress(1.)
            self.opened.emit()
        else:
            self._finishClosed()

    def _finishClosed(self):
        active = self._open or self._progress > 0 or not self.isHidden()
        self._animation.stop()
        self._raiseTimer.stop()
        self._open = False
        self._setProgress(0.)
        QWidget.hide(self)
        focus, self._previousFocus = self._previousFocus, None
        try:
            if focus is not None and focus.isVisible() and self.parentWidget().isVisible():
                focus.setFocus(Qt.OtherFocusReason)
        except RuntimeError:
            pass  # Caller may have deleted the previously focused control.
        if active:
            self.closed.emit()

    def _raiseIfVisible(self):
        if self.isVisible():
            self.raise_()

    def eventFilter(self, watched, event):
        if watched is self.parentWidget():
            if event.type() == QEvent.Resize:
                self.setGeometry(watched.rect())
                self._updatePanelGeometry()
            elif event.type() == QEvent.Hide:
                self._finishClosed()
            elif event.type() in (QEvent.ChildAdded, QEvent.ChildPolished):
                if self.isVisible():
                    self._raiseTimer.start()
        return super().eventFilter(watched, event)

    def resizeEvent(self, event):
        self._updatePanelGeometry()
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._open:  # Also support QWidget.setVisible(True).
            self._previousFocus = QApplication.focusWidget()
            self._open = True
            self.raise_()
            self.setFocus(Qt.PopupFocusReason)
            self._animateTo(1.)

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._open or self._progress > 0:  # External setVisible(False).
            self._finishClosed()

    def mousePressEvent(self, event):
        if (event.button() == Qt.LeftButton and self._maskClosable
                and not self.panel.geometry().contains(event.position().toPoint())):
            self.close()
        event.accept()  # Do not send an outside click to content below the mask.

    def focusNextPrevChild(self, forward):
        # Keep keyboard navigation inside this parent-scoped modal surface.
        widgets = [w for w in self.panel.findChildren(QWidget)
                   if w.isVisible() and w.isEnabled() and w.focusPolicy() & Qt.TabFocus]
        if widgets:
            focus = QApplication.focusWidget()
            index = widgets.index(focus) if focus in widgets else (-1 if forward else 0)
            widgets[(index + (1 if forward else -1)) % len(widgets)].setFocus(
                Qt.TabFocusReason if forward else Qt.BacktabFocusReason)
        else:
            self.setFocus(Qt.TabFocusReason)
        return True

    def _applyTheme(self):
        self.panel.update()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        color = self.maskColor()
        color.setAlpha(round(color.alpha() * self._progress))
        painter.fillRect(self.rect(), color)
