# coding:utf-8
"""Task notifications using the existing InfoBar and progress ring animations."""

from PySide6.QtCore import QAbstractAnimation, Qt, Signal
from PySide6.QtWidgets import QWidget

from ...common.config import qconfig
from .info_bar import InfoBar, InfoBarIcon, InfoBarManager, InfoBarPosition
from .progress_ring import IndeterminateProgressRing, ProgressRing


class _ProgressIconWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.indeterminate = True
        self.busyRing = IndeterminateProgressRing(self, start=False)
        self.valueRing = ProgressRing(self, useAni=False)
        for ring in (self.busyRing, self.valueRing):
            ring.setFixedSize(20, 20)
            ring.setStrokeWidth(3)
            ring.move(8, 8)
            ring.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.valueRing.hide()
        qconfig.themeChangedFinished.connect(self._updateRings)
        qconfig.themeColorChanged.connect(self._updateRings)

    def _updateRings(self):
        self.busyRing.update()
        self.valueRing.update()

    def setIndeterminate(self, enabled):
        self.indeterminate = bool(enabled)
        self.busyRing.setVisible(self.indeterminate)
        self.valueRing.setVisible(not self.indeterminate)
        if self.indeterminate and self.isVisible():
            self.busyRing.start()
        else:
            self.busyRing.stop()

    def showEvent(self, event):
        super().showEvent(event)
        if self.indeterminate:
            if self.busyRing.aniGroup.state() == QAbstractAnimation.Paused:
                self.busyRing.aniGroup.resume()
            else:
                self.busyRing.start()

    def hideEvent(self, event):
        if self.busyRing.aniGroup.state() == QAbstractAnimation.Running:
            self.busyRing.aniGroup.pause()
        super().hideEvent(event)


class ProgressInfoBar(InfoBar):
    """Neutral task notification; indeterminate by default and persistent until closed.

    ``setValue(0..100)`` switches to determinate progress. Closing the notification
    does not cancel the underlying task; connect ``closedSignal`` if appropriate.
    Remaining time is caller-formatted text, not an automatically calculated ETA.
    """

    valueChanged = Signal(int)

    def __init__(self, title, content, orient=Qt.Horizontal, isClosable=True,
                 duration=-1, position=InfoBarPosition.TOP_RIGHT, parent=None):
        self._description = str(content)
        self._remainingTime = ""
        super().__init__(InfoBarIcon.INFORMATION, str(title), self._description,
                         orient, isClosable, duration, position, parent)
        oldIcon = self.iconWidget
        self.iconWidget = _ProgressIconWidget(self)
        self.hBoxLayout.replaceWidget(oldIcon, self.iconWidget)
        oldIcon.hide()
        oldIcon.deleteLater()
        self.progressRing = self.iconWidget.busyRing
        self.determinateRing = self.iconWidget.valueRing
        self.determinateRing.valueChanged.connect(self.valueChanged)
        self._adjustText()

    def setTitle(self, title):
        self.title = str(title)
        self._refreshText()

    def setContent(self, content):
        self._description = str(content)
        self._refreshText()

    def setRemainingTime(self, text):
        """Set an optional suffix such as 'Remaining: 10 s'; empty text removes it."""
        self._remainingTime = str(text)
        self._refreshText()

    def remainingTime(self):
        return self._remainingTime

    def _adjustText(self):
        self.content = " · ".join(filter(None, (self._description, self._remainingTime)))
        self.titleLabel.setVisible(bool(self.title))
        self.contentLabel.setVisible(bool(self.content))
        super()._adjustText()

    def _refreshText(self):
        self._adjustText()
        if not self.isVisible() or not self.parent() or self.position == InfoBarPosition.NONE:
            return
        # Text/ETA updates can change both this bar's width and the stack's height.
        manager = InfoBarManager.make(self.position)
        bars = manager.infoBars.get(self.parent(), [])
        if self not in bars:
            return
        manager.aniGroups[self.parent()].stop()
        for bar in bars:
            slide = bar.property("slideAni")
            if slide:
                slide.stop()
            bar.move(manager._pos(bar))

    def isIndeterminate(self):
        return self.iconWidget.indeterminate

    def setIndeterminate(self, enabled):
        self.iconWidget.setIndeterminate(enabled)

    def setValue(self, value):
        """Set a clamped percentage and switch to determinate progress."""
        self.determinateRing.setValue(max(0, min(100, int(value))))
        self.setIndeterminate(False)
        self.determinateRing.update()

    def value(self):
        return self.determinateRing.value()

    def setCustomBarColor(self, light, dark):
        for ring in (self.progressRing, self.determinateRing):
            ring.setCustomBarColor(light, dark)

    def closeEvent(self, event):
        self.progressRing.stop()
        self.hide()
        super().closeEvent(event)

    @classmethod
    def new(cls, title, content, orient=Qt.Horizontal, isClosable=True,
            duration=-1, position=InfoBarPosition.TOP_RIGHT, parent=None):
        """Create and show a task notification."""
        bar = cls(title, content, orient, isClosable, duration, position, parent)
        bar.show()
        return bar

    # Unlike the other InfoBar status factories, a task bar has a neutral body.
    info = new

    # Completion/warning/error factories retain ordinary InfoBar semantics;
    # they must not pass a status icon to the task-only constructor above.
    success = InfoBar.success
    warning = InfoBar.warning
    error = InfoBar.error
