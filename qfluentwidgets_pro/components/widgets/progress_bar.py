# coding:utf-8
from math import floor
import sys

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QLocale,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRectF,
    QSequentialAnimationGroup,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QHBoxLayout,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...common.icon import FluentIconBase, Icon, Theme, drawIcon
from ...common.style_sheet import ThemeColor, isDarkTheme, themeColor
from .label import BodyLabel


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


class StepProgressBarButton(QPushButton):
    checkedClicked = Signal()

    def __init__(self, icon: FluentIconBase, text: str, parent: QWidget = None):
        super().__init__(text, parent)
        self._icon = icon
        self._hoverProgress = 0.0
        self._hoverAni = QPropertyAnimation(self, b"hoverProgress", self)
        self._hoverAni.setDuration(150)
        self._checkedLockEnabled = False
        self._nonInteractive = False
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(34, 34)

    def setCheckedLockEnabled(self, enabled: bool):
        self._checkedLockEnabled = bool(enabled)

    def isCheckedLockEnabled(self) -> bool:
        return self._checkedLockEnabled

    def setNonInteractive(self, enabled: bool):
        """Set non-interactive mode - no hover/click effects but appearance unchanged"""
        self._nonInteractive = bool(enabled)
        if enabled:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def isNonInteractive(self) -> bool:
        return self._nonInteractive

    def nextCheckState(self):
        if self._nonInteractive:
            return
        if self._checkedLockEnabled and self.isChecked():
            self.checkedClicked.emit()
            return

        super().nextCheckState()

    def getHoverProgress(self) -> float:
        return self._hoverProgress

    def setHoverProgress(self, p: float):
        p = max(0.0, min(1.0, float(p)))
        if p == self._hoverProgress:
            return
        self._hoverProgress = p
        self.update()

    hoverProgress = Property(float, getHoverProgress, setHoverProgress)

    def enterEvent(self, e):
        if self._nonInteractive:
            return
        super().enterEvent(e)
        self._hoverAni.stop()
        self._hoverAni.setEndValue(1.0)
        self._hoverAni.start()

    def leaveEvent(self, e):
        if self._nonInteractive:
            return
        super().leaveEvent(e)
        self._hoverAni.stop()
        self._hoverAni.setEndValue(0.0)
        self._hoverAni.start()

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
        if isinstance(icon, FluentIconBase):
            # reverse icon color: dark theme -> black icon, light theme -> white icon
            theme = Theme.LIGHT if isDarkTheme() else Theme.DARK
            icon = icon.icon(theme)
        elif isinstance(icon, Icon):
            theme = Theme.LIGHT if isDarkTheme() else Theme.DARK
            icon = icon.fluentIcon.icon(theme)

        drawIcon(icon, painter, rect, state)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform
            | QPainter.TextAntialiasing
        )

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        if isDarkTheme():
            borderColor = QColor(255, 255, 255, 13)
            baseBg = QColor(255, 255, 255, 15)
        else:
            borderColor = QColor(0, 0, 0, 19)
            baseBg = QColor(255, 255, 255, 178)

        painter.setPen(Qt.NoPen)

        if self.isChecked() and self._hoverProgress > 0:
            base = themeColor()
            hoverColor = (
                ThemeColor.DARK_3.color()
                if isDarkTheme()
                else ThemeColor.LIGHT_3.color()
            )
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0.0, base)
            gradient.setColorAt(1.0, hoverColor)
            painter.setBrush(base)
            painter.drawEllipse(rect)
            painter.setOpacity(self._hoverProgress)
            painter.setBrush(gradient)
            painter.drawEllipse(rect)
            painter.setOpacity(1.0)
        elif self.isChecked():
            painter.setBrush(themeColor())
        elif self._hoverProgress > 0:
            c1 = themeColor()
            c2 = themeColor()
            c2.setAlpha(180)
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0.0, c1)
            gradient.setColorAt(1.0, c2)
            painter.setBrush(baseBg)
            painter.drawEllipse(rect)
            painter.setOpacity(self._hoverProgress)
            painter.setBrush(gradient)
            painter.drawEllipse(rect)
            painter.setOpacity(1.0)
        else:
            painter.setBrush(baseBg)

        if self._hoverProgress <= 0:
            painter.drawEllipse(rect)

        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        path.addEllipse(rect)
        innerRect = rect.adjusted(1, 1, -1, -1)
        innerPath = QPainterPath()
        innerPath.addEllipse(innerRect)
        painter.setBrush(borderColor)
        painter.drawPath(path.subtracted(innerPath))

        if not self.isEnabled():
            painter.setOpacity(0.43)

        if self.isChecked():
            s = 16
            x = (self.width() - s) / 2
            y = (self.height() - s) / 2
            self._drawIcon(self._icon, painter, QRectF(x, y, s, s), QIcon.On)
            return

        if self._hoverProgress > 0:
            painter.setPen(Qt.white)
        else:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)

        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class StepProgressBar(QWidget):
    """Step progress bar widget

    A widget that displays progress through a series of steps using StepProgressBarButton widgets
    connected by lines.

    Constructors
    ------------
    * StepProgressBar(`parent`: QWidget = None)
    * StepProgressBar(`icon`: FluentIconBase, `count`: int, `parent`: QWidget = None)
    """

    currentChanged = Signal(int)

    def __init__(
        self, icon: FluentIconBase = None, count: int = 4, parent: QWidget = None
    ):
        super().__init__(parent)
        self._icons: list[FluentIconBase] = []
        self._stepNames: list[str] = []
        self._count = count
        self._current = 0
        self._buttons: list[StepProgressBarButton] = []
        self._labels: list[BodyLabel] = []
        self._lineHeight = 3

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)

        # If single icon provided, use it for all buttons
        if icon is not None:
            self._icons = [icon] * count

        self._initButtons()

    def _initButtons(self):
        for i in range(self._count):
            icon = self._icons[i] if i < len(self._icons) else None
            name = self._stepNames[i] if i < len(self._stepNames) else str(i + 1)

            # Create step item with button and label
            stepWidget = QWidget(self)
            vLayout = QVBoxLayout(stepWidget)
            vLayout.setContentsMargins(0, 0, 0, 0)
            vLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn = StepProgressBarButton(icon, str(i + 1), self)
            btn.setCheckedLockEnabled(True)
            btn.clicked.connect(lambda checked, idx=i: self._onButtonClicked(idx))

            label = BodyLabel(name, self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            vLayout.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)
            if sys.platform == 'drawin':
                vLayout.addSpacing(6)
            vLayout.addWidget(label, 0, Qt.AlignmentFlag.AlignHCenter)

            self.hBoxLayout.addWidget(stepWidget)
            self._buttons.append(btn)
            self._labels.append(label)

            # Add stretch for line between buttons
            if i < self._count - 1:
                self.hBoxLayout.addStretch(1)

        self._updateButtonStates()

    def _onButtonClicked(self, index: int):
        if self._buttons[index].isNonInteractive():
            return
        if index != self._current:
            self.setCurrent(index)
        else:
            self._buttons[index].checkedClicked.emit()

    def _updateButtonStates(self):
        for i, btn in enumerate(self._buttons):
            btn.setEnabled(True)

            # First button is always checked
            if i == 0:
                btn.setChecked(True)
            elif i <= self._current:
                btn.setChecked(True)
            else:
                btn.setChecked(False)

    def setCurrent(self, index: int):
        """Set current step index (0-based)"""
        if 0 <= index < self._count and index != self._current:
            self._current = index
            self._updateButtonStates()
            self.currentChanged.emit(index)
            self.update()

    def current(self) -> int:
        """Get current step index"""
        return self._current

    def setCount(self, count: int):
        """Set number of steps"""
        if count > 0 and count != self._count:
            self._count = count
            # Clear existing buttons
            for btn in self._buttons:
                btn.deleteLater()
            self._buttons.clear()

            # Clear layout
            while self.hBoxLayout.count():
                item = self.hBoxLayout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self._initButtons()
            self.update()

    def count(self) -> int:
        """Get number of steps"""
        return self._count

    def setIcon(self, index: int, icon: FluentIconBase):
        """Set icon for a specific button (0-based index)"""
        if 0 <= index < self._count:
            # Extend icons list if needed
            while len(self._icons) <= index:
                self._icons.append(None)
            self._icons[index] = icon
            self._buttons[index]._icon = icon
            self._buttons[index].update()

    def setIcons(self, icons: list[FluentIconBase]):
        """Set icons for all buttons"""
        self._icons = icons.copy()
        for i, btn in enumerate(self._buttons):
            if i < len(icons):
                btn._icon = icons[i]
                btn.update()

    def icon(self, index: int) -> FluentIconBase:
        """Get icon for a specific button (0-based index)"""
        if 0 <= index < len(self._icons):
            return self._icons[index]
        return None

    def setStepName(self, index: int, name: str):
        """Set name for a specific step (0-based index)"""
        if 0 <= index < self._count:
            # Extend stepNames list if needed
            while len(self._stepNames) <= index:
                self._stepNames.append("")
            self._stepNames[index] = name
            self._labels[index].setText(name)

    def setStepNames(self, names: list[str]):
        """Set names for all steps"""
        self._stepNames = names.copy()
        for i, label in enumerate(self._labels):
            if i < len(names):
                label.setText(names[i])

    def stepName(self, index: int) -> str:
        """Get name for a specific step (0-based index)"""
        if 0 <= index < len(self._stepNames):
            return self._stepNames[index]
        return ""

    def setNonInteractive(self, enabled: bool):
        """Set non-interactive mode for all buttons - no hover/click effects"""
        for btn in self._buttons:
            btn.setNonInteractive(enabled)

    def isNonInteractive(self) -> bool:
        """Check if all buttons are non-interactive"""
        return all(btn.isNonInteractive() for btn in self._buttons)

    def nextStep(self):
        """Move to next step"""
        if self._current < self._count - 1:
            self.setCurrent(self._current + 1)

    def previousStep(self):
        """Move to previous step"""
        if self._current > 0:
            self.setCurrent(self._current - 1)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._count < 2:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        for i in range(self._count - 1):
            btn1 = self._buttons[i]
            btn2 = self._buttons[i + 1]

            btnSize = btn1.width()
            radius = btnSize / 2 - 1

            # Get button center position in parent coordinates
            btn1Rect = btn1.geometry()
            btn2Rect = btn2.geometry()
            btn1Center = btn1.parent().mapToParent(btn1Rect.center())
            btn2Center = btn2.parent().mapToParent(btn2Rect.center())

            x1 = btn1Center.x() + radius
            x2 = btn2Center.x() - radius
            y = btn1Center.y()

            # Determine line color based on step completion
            if i < self._current:
                painter.setPen(Qt.NoPen)
                painter.setBrush(themeColor())
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(
                    QColor(255, 255, 255, 17) if isDarkTheme() else QColor(0, 0, 0, 125)
                )

            painter.drawRect(
                x1, y - self._lineHeight // 2, x2 - x1 + 1, self._lineHeight
            )
