# coding:utf-8
from typing import List, Tuple
from PySide6.QtCore import (
    Property,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRectF,
    QSequentialAnimationGroup,
    Qt,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QProgressBar

from ...common.font import setFont
from ...common.style_sheet import isDarkTheme, themeColor
from .progress_bar import ProgressBar


class ProgressRing(ProgressBar):
    """Progress ring"""

    def __init__(self, parent=None, useAni=True):
        super().__init__(parent, useAni=useAni)
        self.lightBackgroundColor = QColor(0, 0, 0, 34)
        self.darkBackgroundColor = QColor(255, 255, 255, 34)
        self._strokeWidth = 6

        self.setTextVisible(False)
        self.setFixedSize(100, 100)
        setFont(self)

    def getStrokeWidth(self):
        return self._strokeWidth

    def setStrokeWidth(self, w: int):
        self._strokeWidth = w
        self.update()

    def _drawText(self, painter: QPainter, text: str):
        """draw text"""
        painter.setFont(self.font())
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        painter.drawText(self.rect(), Qt.AlignCenter, text)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth  # circle thickness
        w = min(self.height(), self.width()) - cw
        rc = QRectF(cw / 2, self.height() / 2 - w / 2, w, w)

        # draw background
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        pen = QPen(bc, cw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(rc, 0, 360 * 16)

        if self.maximum() <= self.minimum():
            return

        # draw bar
        pen.setColor(self.barColor())
        painter.setPen(pen)
        degree = int(self.val / (self.maximum() - self.minimum()) * 360)
        painter.drawArc(rc, 90 * 16, -degree * 16)

        # draw text
        if self.isTextVisible():
            self._drawText(painter, self.valText())

    strokeWidth = Property(int, getStrokeWidth, setStrokeWidth)


class RadialGauge(ProgressRing):
    """Radial gauge with 270° arc (bottom gap) - dashboard style"""

    def __init__(self, parent=None, useAni=True):
        super().__init__(parent, useAni=useAni)
        self._startAngle = 225
        self._spanAngle = 270
        self.setTextVisible(True)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth
        w = min(self.height(), self.width()) - cw
        rc = QRectF(cw / 2, self.height() / 2 - w / 2, w, w)

        # draw background arc (270°)
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        pen = QPen(bc, cw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(rc, int(self._startAngle * 16), int(-self._spanAngle * 16))

        if self.maximum() <= self.minimum():
            return

        # draw progress arc
        pen.setColor(self.barColor())
        painter.setPen(pen)
        progress = self.val / (self.maximum() - self.minimum())
        degree = int(progress * self._spanAngle)
        painter.drawArc(rc, int(self._startAngle * 16), int(-degree * 16))

        # draw text
        if self.isTextVisible():
            self._drawText(painter, self.valText())


class MultiSegmentProgressRing(ProgressRing):
    def __init__(self, parent=None, useAni=True):
        super().__init__(parent=parent, useAni=useAni)
        self._segments: List[Tuple[float, QColor]] = []
        self._gapDegree = 3.0
        self._text = ""

    def segments(self) -> List[Tuple[float, QColor]]:
        return list(self._segments)

    def setSegments(self, segments: List[Tuple[float, QColor]]):
        segs: List[Tuple[float, QColor]] = []
        for p, c in (segments or []):
            segs.append((float(p), QColor(c)))

        self._segments = segs
        self.update()

    def getGapDegree(self) -> float:
        return self._gapDegree

    def setGapDegree(self, deg: float):
        self._gapDegree = max(0.0, float(deg))
        self.update()

    def text(self) -> str:
        return self._text

    def setText(self, text: str):
        self._text = text or ""
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth
        w = min(self.height(), self.width()) - cw
        rc = QRectF(cw / 2, self.height() / 2 - w / 2, w, w)

        radius = w / 2

        if not self._segments:
            return

        total = 0.0
        for p, _ in self._segments:
            if p > 0:
                total += p

        if total <= 0:
            return

        isSingleSegment = len(self._segments) == 1

        gapDeg = 0.0 if isSingleSegment else self._gapDegree
        capDeg = 0.0
        if radius > 0 and not isSingleSegment:
            capDeg = (cw / 2) / radius * 180 / 3.141592653589793

        gapDeg = max(0.0, gapDeg) + 2 * capDeg
        startDeg = 90.0

        for p, color in self._segments:
            slotDeg = max(0.0, p) / total * 360.0
            sweepDeg = max(0.0, slotDeg - gapDeg)
            if sweepDeg > 0:
                pen = QPen(color, cw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.drawArc(
                    rc,
                    int(round(startDeg * 16)),
                    -int(round(sweepDeg * 16)),
                )

            startDeg -= slotDeg

        # draw text
        if self._text:
            self._drawText(painter, self._text)

    gapDegree = Property(float, getGapDegree, setGapDegree)
    textProperty = Property(str, text, setText)


class IndeterminateProgressRing(QProgressBar):
    """Indeterminate progress ring"""

    def __init__(self, parent=None, start=True):
        super().__init__(parent=parent)
        self.lightBackgroundColor = QColor(0, 0, 0, 0)
        self.darkBackgroundColor = QColor(255, 255, 255, 0)
        self._lightBarColor = QColor()
        self._darkBarColor = QColor()
        self._strokeWidth = 6

        self._startAngle = -180
        self._spanAngle = 0

        self.startAngleAni1 = QPropertyAnimation(self, b"startAngle", self)
        self.startAngleAni2 = QPropertyAnimation(self, b"startAngle", self)
        self.spanAngleAni1 = QPropertyAnimation(self, b"spanAngle", self)
        self.spanAngleAni2 = QPropertyAnimation(self, b"spanAngle", self)

        self.startAngleAniGroup = QSequentialAnimationGroup(self)
        self.spanAngleAniGroup = QSequentialAnimationGroup(self)
        self.aniGroup = QParallelAnimationGroup(self)

        # initialize start angle animation
        self.startAngleAni1.setDuration(1000)
        self.startAngleAni1.setStartValue(0)
        self.startAngleAni1.setEndValue(450)

        self.startAngleAni2.setDuration(1000)
        self.startAngleAni2.setStartValue(450)
        self.startAngleAni2.setEndValue(1080)

        self.startAngleAniGroup.addAnimation(self.startAngleAni1)
        self.startAngleAniGroup.addAnimation(self.startAngleAni2)

        # initialize span angle animation
        self.spanAngleAni1.setDuration(1000)
        self.spanAngleAni1.setStartValue(0)
        self.spanAngleAni1.setEndValue(180)

        self.spanAngleAni2.setDuration(1000)
        self.spanAngleAni2.setStartValue(180)
        self.spanAngleAni2.setEndValue(0)

        self.spanAngleAniGroup.addAnimation(self.spanAngleAni1)
        self.spanAngleAniGroup.addAnimation(self.spanAngleAni2)

        self.aniGroup.addAnimation(self.startAngleAniGroup)
        self.aniGroup.addAnimation(self.spanAngleAniGroup)
        self.aniGroup.setLoopCount(-1)

        self.setFixedSize(80, 80)

        if start:
            self.start()

    @Property(int)
    def startAngle(self):
        return self._startAngle

    @startAngle.setter
    def startAngle(self, angle: int):
        self._startAngle = angle
        self.update()

    @Property(int)
    def spanAngle(self):
        return self._spanAngle

    @spanAngle.setter
    def spanAngle(self, angle: int):
        self._spanAngle = angle
        self.update()

    def getStrokeWidth(self):
        return self._strokeWidth

    def setStrokeWidth(self, w: int):
        self._strokeWidth = w
        self.update()

    def start(self):
        """start spin"""
        self._startAngle = 0
        self._spanAngle = 0
        self.aniGroup.start()

    def stop(self):
        """stop spin"""
        self.aniGroup.stop()
        self.startAngle = 0
        self.spanAngle = 0

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

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth
        w = min(self.height(), self.width()) - cw
        rc = QRectF(cw / 2, self.height() / 2 - w / 2, w, w)

        # draw background
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        pen = QPen(bc, cw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(rc, 0, 360 * 16)

        # draw bar
        pen.setColor(self.darkBarColor() if isDarkTheme() else self.lightBarColor())
        painter.setPen(pen)

        startAngle = -self.startAngle + 180
        painter.drawArc(rc, (startAngle % 360) * 16, -self.spanAngle * 16)

    strokeWidth = Property(int, getStrokeWidth, setStrokeWidth)
