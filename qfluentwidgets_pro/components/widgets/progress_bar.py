# coding:utf-8
from math import floor

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QLocale,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRectF,
    QSequentialAnimationGroup,
    Qt,
)
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import QProgressBar, QSizePolicy

from ...common.icon import FluentIconBase, Icon, drawIcon
from ...common.style_sheet import isDarkTheme, themeColor


class ProgressBar(QProgressBar):
    def __init__(self, parent=None, useAni=True):
        super().__init__(parent)
        self._val = 0
        self.setFixedHeight(4)

        self._useAni = useAni
        self.lightBackgroundColor = QColor(0, 0, 0, 155)
        self.darkBackgroundColor = QColor(255, 255, 255, 155)
        self._lightBarColor = QColor()
        self._darkBarColor = QColor()
        self.ani = QPropertyAnimation(self, b"val", self)

        self._isPaused = False
        self._isError = False
        self.valueChanged.connect(self._onValueChanged)
        self.setValue(0)

    def getVal(self):
        return self._val

    def setVal(self, v: float):
        self._val = v
        self.update()

    def isUseAni(self):
        return self._useAni

    def setUseAni(self, isUSe: bool):
        self._useAni = isUSe

    def _onValueChanged(self, value):
        if not self.useAni:
            self._val = value
            return

        self.ani.stop()
        self.ani.setEndValue(value)
        self.ani.setDuration(150)
        self.ani.start()
        super().setValue(value)

    def lightBarColor(self):
        return self._lightBarColor if self._lightBarColor.isValid() else themeColor()

    def darkBarColor(self):
        return self._darkBarColor if self._darkBarColor.isValid() else themeColor()

    def setCustomBarColor(self, light, dark):
        """set the custom bar color

        Parameters
        ----------
        light, dark: str | Qt.GlobalColor | QColor
            bar color in light/dark theme mode
        """
        self._lightBarColor = QColor(light)
        self._darkBarColor = QColor(dark)
        self.update()

    def setCustomBackgroundColor(self, light, dark):
        """set the custom background color

        Parameters
        ----------
        light, dark: str | Qt.GlobalColor | QColor
            background color in light/dark theme mode
        """
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(dark)
        self.update()

    def resume(self):
        self._isPaused = False
        self._isError = False
        self.update()

    def pause(self):
        self._isPaused = True
        self.update()

    def setPaused(self, isPaused: bool):
        self._isPaused = isPaused
        self.update()

    def isPaused(self):
        return self._isPaused

    def error(self):
        self._isError = True
        self.update()

    def setError(self, isError: bool):
        self._isError = isError
        if isError:
            self.error()
        else:
            self.resume()

    def isError(self):
        return self._isError

    def barColor(self):
        if self.isPaused():
            return QColor(252, 225, 0) if isDarkTheme() else QColor(157, 93, 0)

        if self.isError():
            return QColor(255, 153, 164) if isDarkTheme() else QColor(196, 43, 28)

        return self.darkBarColor() if isDarkTheme() else self.lightBarColor()

    def valText(self):
        if self.maximum() <= self.minimum():
            return ""

        total = self.maximum() - self.minimum()
        result = self.format()
        locale = self.locale()
        locale.setNumberOptions(locale.numberOptions() | QLocale.OmitGroupSeparator)
        result = result.replace("%m", locale.toString(total))
        result = result.replace("%v", locale.toString(self.val))

        if total == 0:
            return result.replace("%p", locale.toString(100))

        progress = int((self.val - self.minimum()) * 100 / total)
        return result.replace("%p", locale.toString(progress))

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        # draw background
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        painter.setPen(bc)
        y = floor(self.height() / 2)
        painter.drawLine(0, y, self.width(), y)

        if self.minimum() >= self.maximum():
            return

        # draw bar
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.barColor())
        w = int(self.val / (self.maximum() - self.minimum()) * self.width())
        r = self.height() / 2
        painter.drawRoundedRect(0, 0, w, self.height(), r, r)

    useAni = Property(bool, isUseAni, setUseAni)
    val = Property(float, getVal, setVal)


class IndeterminateProgressBar(QProgressBar):
    """Indeterminate progress bar"""

    def __init__(self, parent=None, start=True):
        super().__init__(parent=parent)
        self._shortPos = 0
        self._longPos = 0
        self.shortBarAni = QPropertyAnimation(self, b"shortPos", self)
        self.longBarAni = QPropertyAnimation(self, b"longPos", self)

        self._lightBarColor = QColor()
        self._darkBarColor = QColor()

        self._isError = False

        self.aniGroup = QParallelAnimationGroup(self)
        self.longBarAniGroup = QSequentialAnimationGroup(self)

        self.shortBarAni.setDuration(833)
        self.longBarAni.setDuration(1167)
        self.shortBarAni.setStartValue(0)
        self.longBarAni.setStartValue(0)
        self.shortBarAni.setEndValue(1.45)
        self.longBarAni.setEndValue(1.75)
        self.longBarAni.setEasingCurve(QEasingCurve.OutQuad)

        self.aniGroup.addAnimation(self.shortBarAni)
        self.longBarAniGroup.addPause(785)
        self.longBarAniGroup.addAnimation(self.longBarAni)
        self.aniGroup.addAnimation(self.longBarAniGroup)
        self.aniGroup.setLoopCount(-1)

        self.setFixedHeight(4)

        if start:
            self.start()

    def lightBarColor(self):
        return self._lightBarColor if self._lightBarColor.isValid() else themeColor()

    def darkBarColor(self):
        return self._darkBarColor if self._darkBarColor.isValid() else themeColor()

    def setCustomBarColor(self, light, dark):
        """set the custom bar color

        Parameters
        ----------
        light, dark: str | Qt.GlobalColor | QColor
            bar color in light/dark theme mode
        """
        self._lightBarColor = QColor(light)
        self._darkBarColor = QColor(dark)
        self.update()

    @Property(float)
    def shortPos(self):
        return self._shortPos

    @shortPos.setter
    def shortPos(self, p):
        self._shortPos = p
        self.update()

    @Property(float)
    def longPos(self):
        return self._longPos

    @longPos.setter
    def longPos(self, p):
        self._longPos = p
        self.update()

    def start(self):
        self.shortPos = 0
        self.longPos = 0
        self.aniGroup.start()
        self.update()

    def stop(self):
        self.aniGroup.stop()
        self.shortPos = 0
        self.longPos = 0
        self.update()

    def isStarted(self):
        return self.aniGroup.state() == QParallelAnimationGroup.Running

    def pause(self):
        self.aniGroup.pause()
        self.update()

    def resume(self):
        self.aniGroup.resume()
        self.update()

    def setPaused(self, isPaused: bool):
        self.aniGroup.setPaused(isPaused)
        self.update()

    def isPaused(self):
        return self.aniGroup.state() == QParallelAnimationGroup.Paused

    def error(self):
        self._isError = True
        self.aniGroup.stop()
        self.update()

    def setError(self, isError: bool):
        self._isError = isError
        if isError:
            self.error()
        else:
            self.start()

    def isError(self):
        return self._isError

    def barColor(self):
        if self.isError():
            return QColor(255, 153, 164) if isDarkTheme() else QColor(196, 43, 28)

        if self.isPaused():
            return QColor(252, 225, 0) if isDarkTheme() else QColor(157, 93, 0)

        return self.darkBarColor() if isDarkTheme() else self.lightBarColor()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.barColor())

        # draw short bar
        x = int((self.shortPos - 0.4) * self.width())
        w = int(0.4 * self.width())
        r = self.height() / 2
        painter.drawRoundedRect(x, 0, w, self.height(), r, r)

        # draw long bar
        x = int((self.longPos - 0.6) * self.width())
        w = int(0.6 * self.width())
        r = self.height() / 2
        painter.drawRoundedRect(x, 0, w, self.height(), r, r)


class FilledProgressBar(ProgressBar):
    """Vertical filled progress bar with optional icon at the bottom

    Constructors
    ------------
    * FilledProgressBar(`parent`: QWidget = None)
    * FilledProgressBar(`icon`: FluentIconBase | QIcon | str, `parent`: QWidget = None)
    """

    def __init__(self, parent=None, useAni=True):
        super().__init__(parent=parent, useAni=useAni)
        self._icon = None
        self.setFixedWidth(34)
        self.setFixedHeight(210)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCustomBarColor(QColor(33, 148, 243), QColor(33, 148, 243))
        self.setCustomBackgroundColor(QColor(0, 0, 0, 21), QColor(255, 255, 255, 30))

    def setIcon(self, icon):
        """Set the icon to display at the bottom of progress bar

        Parameters
        ----------
        icon: FluentIconBase | QIcon | str
            the icon to be displayed
        """
        self._icon = icon
        self.update()

    def icon(self):
        """Get the icon"""
        return self._icon

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """draw icon in white color"""
        if isinstance(icon, FluentIconBase):
            icon.render(painter, rect, fill=QColor(255, 255, 255).name())
        elif isinstance(icon, Icon):
            icon.fluentIcon.render(painter, rect, fill=QColor(255, 255, 255).name())
        else:
            drawIcon(icon, painter, rect, state)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        textHeight = 20
        gap = 6
        barTop = textHeight + gap
        barRect = QRectF(0, barTop, self.width(), max(0, self.height() - barTop))

        # draw percentage text above progress bar (outside)
        text = self.valText()
        if text:
            painter.setPen(QColor(255, 255, 255) if isDarkTheme() else QColor(0, 0, 0))
            painter.drawText(
                0,
                2,
                self.width(),
                textHeight,
                Qt.AlignHCenter | Qt.AlignVCenter,
                text,
            )

        # draw background
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        painter.setPen(Qt.NoPen)
        painter.setBrush(bc)
        r = self.width() / 2
        painter.drawRoundedRect(barRect, r, r)

        if self.minimum() >= self.maximum():
            return

        # draw bar (from bottom to top)
        painter.setBrush(self.barColor())
        barHeight = int(self.val / (self.maximum() - self.minimum()) * barRect.height())
        painter.drawRoundedRect(
            QRectF(
                barRect.x(),
                barRect.bottom() - barHeight,
                barRect.width(),
                barHeight,
            ),
            r,
            r,
        )

        # draw icon at the bottom
        if self._icon:
            iconSize = 16
            x = (self.width() - iconSize) // 2
            y = int(barRect.bottom() - iconSize - 8)  # bottom padding
            rect = QRectF(x, y, iconSize, iconSize)
            self._drawIcon(self._icon, painter, rect)
