"""Compact, Esc-cancelable waiting dialog using the existing progress ring."""

from PySide6.QtCore import QCoreApplication, QEasingCurve, QEvent, QPropertyAnimation, QRect, QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QDialog, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLayout, QVBoxLayout, QWidget

from ...common.config import qconfig
from ...common.style_sheet import FluentStyleSheet
from ..widgets.progress_ring import IndeterminateProgressRing
from .mask_dialog_base import MaskDialogBase


class WaitingDialog(MaskDialogBase):
    """A 300x132 logical-pixel waiting panel with a window-modal mask.

    Use ``open()`` for non-blocking display. Esc/reject() cancels (``rejected``),
    accept() completes (``accepted``). This is only a UI: connect rejected to
    your worker's cancellation method if the task itself should stop.
    The ring runs only while visible and stops immediately when closing starts.
    """

    def __init__(self, title=None, content='', parent=None):
        if parent is None:
            raise ValueError('WaitingDialog requires a parent window')
        self._ownerWindow = parent.window()
        self._closing = False
        self._filterInstalled = False
        self._resultCode = QDialog.Rejected
        super().__init__(self._ownerWindow)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModal)
        self.setFocusPolicy(Qt.StrongFocus)
        self.progressRing = IndeterminateProgressRing(self.widget, start=False)
        self.progressRing.setFixedSize(56, 56)
        self.progressRing.setStrokeWidth(6)
        self.titleLabel = QLabel(self.widget, objectName='titleLabel')
        self.contentLabel = QLabel(self.widget, objectName='contentLabel')
        for label in (self.titleLabel, self.contentLabel):
            label.setTextFormat(Qt.PlainText)
            label.setWordWrap(True)
            label.setMinimumWidth(0)
            label.setFocusPolicy(Qt.NoFocus)
        self.textLayout = QVBoxLayout()
        self.textLayout.setContentsMargins(0, 0, 0, 0)
        self.textLayout.setSpacing(10)
        self.textLayout.setAlignment(Qt.AlignVCenter)
        self.textLayout.addWidget(self.titleLabel)
        self.textLayout.addWidget(self.contentLabel)
        self.contentLayout = QHBoxLayout(self.widget)
        self.contentLayout.setContentsMargins(39, 32, 29, 32)
        self.contentLayout.setSpacing(30)
        self.contentLayout.addWidget(self.progressRing, 0, Qt.AlignVCenter)
        self.contentLayout.addLayout(self.textLayout, 1)
        self._hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self._hBoxLayout.setSizeConstraint(QLayout.SetNoConstraint)
        self._hBoxLayout.removeWidget(self.widget)
        self._hBoxLayout.addWidget(self.widget, 0, Qt.AlignCenter)
        FluentStyleSheet.DIALOG.apply(self)
        self.setMaskColor(QColor(0, 0, 0, 76))
        self._opacityAnimation = QPropertyAnimation(self)
        self._opacityAnimation.finished.connect(self._finishFade)
        qconfig.themeColorChanged.connect(self.progressRing.update)
        qconfig.themeChangedFinished.connect(self.progressRing.update)
        if title is None:
            title = QCoreApplication.translate('WaitingDialog', 'Please wait...')
        self.setTitle(title)
        self.setContent(content)

    def title(self):
        return self.titleLabel.text()

    def setTitle(self, title):
        self.titleLabel.setText(str(title))
        self.titleLabel.setVisible(bool(title))
        self.setWindowTitle(str(title))
        self._fitToOwner()

    def content(self):
        return self.contentLabel.text()

    def setContent(self, content):
        self.contentLabel.setText(str(content))
        self.contentLabel.setVisible(bool(content))
        self._fitToOwner()

    def _fitToOwner(self):
        owner = self._ownerWindow
        self.setGeometry(QRect(owner.mapToGlobal(QPoint()), owner.size()))
        width = min(300, max(1, owner.width() - 24))
        # Keep normal reference geometry, and wrap gracefully in smaller windows.
        compact = width < 280
        left, right, gap = (16, 16, 16) if compact else (39, 29, 30)
        ringSize = 40 if compact else 56
        self.progressRing.setFixedSize(ringSize, ringSize)
        self.contentLayout.setContentsMargins(left, 32, right, 32)
        self.contentLayout.setSpacing(gap)
        textWidth = max(1, width - left - right - gap - ringSize - 2)
        labels = [label for label in (self.titleLabel, self.contentLabel) if not label.isHidden()]
        for label in labels:
            label.ensurePolished()
        textHeight = sum(max(0, label.heightForWidth(textWidth)) for label in labels)
        if len(labels) > 1:
            textHeight += self.textLayout.spacing()
        height = max(132, max(ringSize, textHeight) + 66)
        self.widget.setFixedSize(width, min(height, max(1, owner.height() - 24)))

    def _animateOpacity(self, start, end, duration):
        # Own the transition so an early Esc cannot let the old fade-in callback
        # clear a newer fade-out effect (MaskDialogBase animations are untracked).
        self._opacityAnimation.stop()
        self._opacityAnimation.setTargetObject(None)
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        self._opacityAnimation.setTargetObject(effect)
        self._opacityAnimation.setPropertyName(b'opacity')
        self._opacityAnimation.setStartValue(start)
        self._opacityAnimation.setEndValue(end)
        self._opacityAnimation.setDuration(duration)
        self._opacityAnimation.setEasingCurve(QEasingCurve.InSine)
        self._opacityAnimation.start()

    def showEvent(self, event):
        self._closing = False
        self._fitToOwner()
        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.progressRing.start()
        QApplication.instance().installEventFilter(self)
        self._filterInstalled = True
        self._animateOpacity(0, 1, 200)
        QDialog.showEvent(self, event)
        self.setFocus(Qt.OtherFocusReason)

    def _stopWaiting(self):
        self.progressRing.stop()
        if self._filterInstalled:
            QApplication.instance().removeEventFilter(self)
            self._filterInstalled = False

    def done(self, code):
        if self._closing:
            return
        self._closing = True
        self._resultCode = int(code)
        self._stopWaiting()
        if not self.isVisible():
            QDialog.done(self, code)
            return
        effect = self.graphicsEffect()
        opacity = effect.opacity() if isinstance(effect, QGraphicsOpacityEffect) else 1
        self.widget.setGraphicsEffect(None)
        self._animateOpacity(opacity, 0, 100)

    def _finishFade(self):
        self._opacityAnimation.setTargetObject(None)
        self.setGraphicsEffect(None)
        if self._closing:
            QDialog.done(self, self._resultCode)

    def hideEvent(self, event):
        self._stopWaiting()
        self._opacityAnimation.stop()
        self._opacityAnimation.setTargetObject(None)
        self.setGraphicsEffect(None)
        QDialog.hideEvent(self, event)

    def eventFilter(self, obj, event):
        if self._filterInstalled:
            kind = event.type()
            if obj is self._ownerWindow:
                if kind in (QEvent.Resize, QEvent.Move):
                    self._fitToOwner()
                elif kind in (QEvent.Hide, QEvent.Close):
                    self.reject()
            inDialog = isinstance(obj, QWidget) and (obj is self or self.isAncestorOf(obj))
            if inDialog and kind == QEvent.ShortcutOverride:
                event.accept()
                return True
            if inDialog and kind == QEvent.KeyPress and event.key() == Qt.Key_Escape:
                event.accept()
                if not event.isAutoRepeat():
                    self.reject()
                return True
        return super().eventFilter(obj, event)
