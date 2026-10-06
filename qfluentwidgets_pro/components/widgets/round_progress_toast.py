# coding:utf-8
"""Capsule-shaped loading notification using the standard indeterminate ring."""

from PySide6.QtCore import QAbstractAnimation, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QLayout

from ...common.config import qconfig
from ...common.style_sheet import isDarkTheme, themeColor
from .progress_ring import IndeterminateProgressRing
from .toast import Toast, ToastPosition


class RoundProgressToast(Toast):
    """Pill-shaped loading toast with an accent-colored indeterminate ring.

    No close button or status stripe. Call ``close()`` when the task ends, or
    supply a nonnegative duration in milliseconds for automatic dismissal.
    """

    def __init__(self, content=None, duration=-1,
                 position=ToastPosition.TOP_RIGHT, parent=None):
        # Translate only the built-in default, never caller-provided content.
        if content is None:
            content = self.tr('Loading, please wait')
        super().__init__("", str(content), duration, False, position,
                         Qt.Horizontal, themeColor(), parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.progressRing = IndeterminateProgressRing(self, start=False)
        self.progressRing.setFixedSize(20, 20)
        self.progressRing.setStrokeWidth(3)
        self.progressRing.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.textLayout.takeAt(0)  # hidden title
        self.textLayout.takeAt(0)  # title/content separator
        self.hBoxLayout.takeAt(2)  # spacing before the hidden close button
        self.textLayout.setAlignment(Qt.AlignVCenter)
        self.textLayout.setAlignment(self.contentLabel, Qt.AlignVCenter)
        self.hBoxLayout.insertWidget(0, self.progressRing, 0, Qt.AlignVCenter)
        self.hBoxLayout.insertSpacing(1, 10)
        self.hBoxLayout.setContentsMargins(20, 14, 30, 14)
        self.hBoxLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.setMinimumSize(180, 48)
        self.shadowEffect.setBlurRadius(16)
        self.shadowEffect.setOffset(0, 3)
        self.shadowEffect.setColor(QColor(0, 0, 0, 32))
        qconfig.themeChangedFinished.connect(self.progressRing.update)
        qconfig.themeColorChanged.connect(self.progressRing.update)
        self._adjustText()

    def _adjustText(self):
        super()._adjustText()
        self.textLayout.invalidate()
        self.hBoxLayout.invalidate()
        self.hBoxLayout.activate()
        self.adjustSize()

    def setContent(self, content):
        self.content = str(content)
        self.contentLabel.setVisible(bool(self.content))
        self._adjustText()
        if self.isVisible() and self in self.manager.toastInfoBars:
            self.manager._adjustPosition()

    def showEvent(self, event):
        super().showEvent(event)
        if self.progressRing.aniGroup.state() == QAbstractAnimation.Paused:
            self.progressRing.aniGroup.resume()
        else:
            self.progressRing.start()

    def hideEvent(self, event):
        if self.progressRing.aniGroup.state() == QAbstractAnimation.Running:
            self.progressRing.aniGroup.pause()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.progressRing.stop()
        super().closeEvent(event)

    def paintEvent(self, event):
        QFrame.paintEvent(self, event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#1D1D1D" if isDarkTheme() else "#E5E5E5"), 1))
        painter.setBrush(self.backgroundColor or QColor("#272727" if isDarkTheme() else "#F7F7F7"))
        rect = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        radius = rect.height() / 2
        painter.drawRoundedRect(rect, radius, radius)

    @classmethod
    def new(cls, content=None, duration=-1,
            position=ToastPosition.TOP_RIGHT, parent=None):
        bar = cls(content, duration, position, parent)
        bar.show()
        return bar

    info = new
    # Terminal status notifications retain ordinary Toast semantics rather than
    # passing an incompatible status color to this loading-only constructor.
    success = Toast.success
    warning = Toast.warning
    error = Toast.error
    custom = Toast.custom
