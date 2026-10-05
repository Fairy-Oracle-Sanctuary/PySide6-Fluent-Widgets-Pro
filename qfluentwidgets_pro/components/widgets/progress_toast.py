# coding:utf-8
"""Compact task notifications with a status icon and bottom progress stripe."""

from PySide6.QtCore import Property, QPropertyAnimation, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QLayout, QWidget

from ...common.config import qconfig
from ...common.icon import Theme, isDarkTheme
from ...common.style_sheet import themeColor
from .info_bar import InfoBarIcon
from .toast import Toast, ToastPosition


class _ProgressToastIcon(QWidget):
    def __init__(self, toast):
        super().__init__(toast)
        self.toast = toast
        self.setFixedSize(16, 16)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = self.toast.barColor()
        # Preserve the existing vector glyph and choose its readable contrast.
        brightness = color.red() * .2126 + color.green() * .7152 + color.blue() * .0722
        theme = Theme.DARK if brightness > 160 else Theme.LIGHT
        self.toast.icon().render(
            painter, QRectF(self.rect()), theme, indexes=[0],
            **{"fill": color.name(), "fill-opacity": str(color.alphaF())}
        )


class ProgressToast(Toast):
    """Persistent compact task toast; values are percentages in the range 0..100.

    Progress, message and status are independent. Reaching 100 does not change
    the status or close the toast. Closing does not cancel the underlying task.
    Status colors can be configured individually for light and dark themes.
    """

    valueChanged = Signal(int)

    _stateColors = {
        InfoBarIcon.SUCCESS: ("#0F7B0F", "#6CCB5F"),
        InfoBarIcon.WARNING: ("#9D5D00", "#FCE100"),
        InfoBarIcon.ERROR: ("#C42B1C", "#FF99A4"),
    }

    def __init__(self, content, icon=InfoBarIcon.INFORMATION, value=0,
                 duration=-1, isClosable=True, position=ToastPosition.TOP_RIGHT,
                 parent=None):
        self._checkIcon(icon)
        self._icon = icon
        self._colors = {}
        self._customColors = None
        self._value = max(0, min(100, int(value)))
        self._progress = float(self._value)
        self._useAni = True
        super().__init__("", str(content), duration, isClosable, position,
                         Qt.Horizontal, self.barColor(), parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._progressAni = QPropertyAnimation(self, b"progress", self)
        self._progressAni.setDuration(150)
        self.iconWidget = _ProgressToastIcon(self)
        # Keep Toast's close button, shadow, custom-widget area and manager.
        self.textLayout.takeAt(0)  # hidden title
        self.textLayout.takeAt(0)  # title/content separator
        self.textLayout.setAlignment(Qt.AlignVCenter)
        self.textLayout.setAlignment(self.contentLabel, Qt.AlignVCenter)
        self.hBoxLayout.setContentsMargins(12, 10, 12, 10)
        self.hBoxLayout.setAlignment(self.closeButton, Qt.AlignVCenter)
        self.hBoxLayout.insertWidget(0, self.iconWidget, 0, Qt.AlignVCenter)
        self.hBoxLayout.insertSpacing(1, 10)
        self.hBoxLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.setMinimumSize(280, 50)
        qconfig.themeChangedFinished.connect(self._updateAppearance)
        qconfig.themeColorChanged.connect(self._updateAppearance)
        self._adjustText()

    @staticmethod
    def _checkIcon(icon):
        if not isinstance(icon, InfoBarIcon):
            raise ValueError("ProgressToast status must be an InfoBarIcon")

    def icon(self):
        return self._icon

    def setIcon(self, icon):
        self._checkIcon(icon)
        self._icon = icon
        self._updateAppearance()

    def _updateAppearance(self):
        self.toastColor = self.barColor()
        self.iconWidget.update()
        self.update()

    def barColor(self):
        colors = self._colors.get(self._icon, self._customColors)
        if colors is None:
            colors = self._stateColors.get(self._icon)
        if colors is None:
            return themeColor()
        return QColor(colors[1 if isDarkTheme() else 0])

    @staticmethod
    def _colorPair(light, dark):
        colors = (QColor(light), QColor(light if dark is None else dark))
        if not all(color.isValid() for color in colors):
            raise ValueError("Invalid ProgressToast color")
        return colors

    def setStateColor(self, icon, light, dark=None):
        """Configure an individual status; omitted dark color uses light in both themes."""
        self._checkIcon(icon)
        self._colors[icon] = self._colorPair(light, dark)
        self._updateAppearance()

    def setCustomBarColor(self, light, dark=None):
        """Set the icon/stripe fallback for all statuses without a per-state override."""
        self._customColors = self._colorPair(light, dark)
        self._updateAppearance()

    def setContent(self, content):
        self.content = str(content)
        self.contentLabel.setVisible(bool(self.content))
        self._adjustText()
        if self.isVisible() and self in self.manager.toastInfoBars:
            self.manager._adjustPosition()

    def _adjustText(self):
        super()._adjustText()
        # QLabel changes invalidate nested layout hints asynchronously. Resolve
        # them now so the manager sees the new height when restacking messages.
        self.textLayout.invalidate()
        self.hBoxLayout.invalidate()
        self.hBoxLayout.activate()
        self.adjustSize()

    def value(self):
        return self._value

    def setValue(self, value):
        value = max(0, min(100, int(value)))
        if value == self._value:
            return
        self._value = value
        self._progressAni.stop()
        if self._useAni and self.isVisible():
            self._progressAni.setStartValue(self._progress)
            self._progressAni.setEndValue(value)
            self._progressAni.start()
        else:
            self._setProgress(value)
        self.valueChanged.emit(value)

    def isUseAni(self):
        return self._useAni

    def setUseAni(self, enabled):
        self._useAni = bool(enabled)
        if not self._useAni:
            self._progressAni.stop()
            self._setProgress(self._value)

    def _getProgress(self):
        return self._progress

    def _setProgress(self, value):
        self._progress = float(value)
        self.update()

    progress = Property(float, _getProgress, _setProgress)

    def paintEvent(self, event):
        # Deliberately bypass Toast's top status stripe.
        QFrame.paintEvent(self, event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        shape = QPainterPath()
        shape.addRoundedRect(QRectF(.5, .5, w - 1, h - 1), 8, 8)
        painter.setPen(QPen(QColor("#484848" if isDarkTheme() else "#E5E5E5"), 1))
        painter.setBrush(self.backgroundColor or QColor("#323232" if isDarkTheme() else "#F7F7F7"))
        painter.drawPath(shape)
        # One shared clipping path keeps both full and partial progress inside
        # the rounded lower corners, while the moving end remains flat.
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), 8, 8)
        painter.setClipPath(clip)
        painter.fillRect(QRectF(0, h - 3, w * self._progress / 100, 3), self.barColor())

    def closeEvent(self, event):
        self._progressAni.stop()
        super().closeEvent(event)

    @classmethod
    def new(cls, content, icon=InfoBarIcon.INFORMATION, value=0, duration=-1,
            isClosable=True, position=ToastPosition.TOP_RIGHT, parent=None):
        bar = cls(content, icon, value, duration, isClosable, position, parent)
        bar.show()
        return bar

    @classmethod
    def info(cls, content, value=0, **kwargs):
        return cls.new(content, InfoBarIcon.INFORMATION, value, **kwargs)

    @classmethod
    def success(cls, content, value=100, **kwargs):
        return cls.new(content, InfoBarIcon.SUCCESS, value, **kwargs)

    @classmethod
    def warning(cls, content, value=0, **kwargs):
        return cls.new(content, InfoBarIcon.WARNING, value, **kwargs)

    @classmethod
    def error(cls, content, value=0, **kwargs):
        return cls.new(content, InfoBarIcon.ERROR, value, **kwargs)

    @classmethod
    def custom(cls, content, color, value=0, icon=InfoBarIcon.INFORMATION,
               darkColor=None, **kwargs):
        bar = cls(content, icon, value, **kwargs)
        bar.setCustomBarColor(color, darkColor)
        bar.show()
        return bar
