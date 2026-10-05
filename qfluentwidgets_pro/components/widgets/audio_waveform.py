"""Lightweight, transparent PCM waveform view; no multimedia imports."""
from array import array
from math import isfinite
from operator import index

from PySide6.QtCore import QLineF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ...common.config import qconfig
from ...common.style_sheet import isDarkTheme


class AudioWaveformWidget(QWidget):
    """Display normalized mono samples (-1..1) and an optional play position.

    Sample data is copied into compact float arrays. Completed 128-frame blocks
    cache their extrema, so resize/append need not rescan the entire recording.
    Painting and position updates only visit the visible bars. All setters must
    run on the widget's GUI thread; use queued signals for background producers.
    """

    samplesChanged = Signal()
    durationChanged = Signal(int)
    positionChanged = Signal(int)
    seekRequested = Signal(int)
    _blockSize = 128

    def __init__(self, parent=None):
        super().__init__(parent)
        self._samples = array('f')
        self._blockMin = array('f')
        self._blockMax = array('f')
        self._sampleRate = 24000
        self._position = 0
        self._barWidth = 1.5
        self._barSpacing = 2.0
        self._amplitudeScale = 1.0
        self._bars = []
        self._seekEnabled = True
        self._dragging = False
        self._lightWaveformColor = QColor('#D6D6D6')
        self._darkWaveformColor = QColor('#686868')
        self._lightPlayedColor = QColor('#606060')
        self._darkPlayedColor = QColor('#F2F2F2')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName(self.tr('Audio waveform'))
        qconfig.themeChangedFinished.connect(self.update)

    @staticmethod
    def _validateRate(rate):
        if isinstance(rate, bool):
            raise ValueError('sampleRate must be a positive integer')
        try:
            rate = index(rate)
        except TypeError as error:
            raise ValueError('sampleRate must be a positive integer') from error
        if rate <= 0:
            raise ValueError('sampleRate must be a positive integer')
        return rate

    @staticmethod
    def _copySamples(samples):
        if isinstance(samples, (bytes, bytearray, str)):
            raise TypeError('Pass normalized numeric samples, not encoded audio/PCM bytes')
        result = array('f')
        for value in samples:
            value = float(value)
            if not isfinite(value):
                raise ValueError('Audio samples must be finite')
            result.append(max(-1.0, min(1.0, value)))
        return result

    def setSamples(self, samples, sampleRate=24000):
        """Replace the recording; clamp finite samples to -1..1 and reset position."""
        rate = self._validateRate(sampleRate)
        data = self._copySamples(samples)
        oldDuration = self.duration()
        self._samples = data
        self._sampleRate = rate
        self._blockMin = array('f')
        self._blockMax = array('f')
        self._cacheBlocks()
        self._rebuildBars()
        self.setPosition(0)
        self._notifySamples(oldDuration)

    def appendSamples(self, samples, sampleRate=None):
        """Append a TTS chunk without renormalizing or moving existing progress.

        sampleRate may be omitted, or must match the existing nonempty stream.
        An empty widget adopts the supplied rate. Validation is transactional.
        """
        rate = self._sampleRate if sampleRate is None else self._validateRate(sampleRate)
        if self._samples and rate != self._sampleRate:
            raise ValueError('Cannot append samples with a different sample rate; clear first')
        data = self._copySamples(samples)
        if not data:
            return
        oldDuration = self.duration()
        self._samples.extend(data)
        self._sampleRate = rate
        self._cacheBlocks()
        self._rebuildBars()
        self._notifySamples(oldDuration)

    def clear(self):
        self.setSamples([], self._sampleRate)

    def samples(self):
        """Return an independent float-array copy of the recording."""
        return array('f', self._samples)

    def sampleCount(self):
        return len(self._samples)

    def sampleRate(self):
        return self._sampleRate

    def duration(self):
        """Duration in milliseconds, rounded up to retain very short recordings."""
        return (len(self._samples) * 1000 + self._sampleRate - 1) // self._sampleRate

    def position(self):
        return self._position

    def setPosition(self, milliseconds):
        value = max(0, min(self.duration(), int(milliseconds)))
        if value == self._position:
            return
        self._position = value
        self.positionChanged.emit(value)
        self.update()

    def _notifySamples(self, oldDuration):
        self.setAccessibleDescription(self.tr('Duration: %1 ms').replace('%1', str(self.duration())))
        self.samplesChanged.emit()
        if oldDuration != self.duration():
            self.durationChanged.emit(self.duration())
        self.update()

    def _cacheBlocks(self):
        start = len(self._blockMin) * self._blockSize
        stop = len(self._samples) // self._blockSize * self._blockSize
        for offset in range(start, stop, self._blockSize):
            block = self._samples[offset:offset + self._blockSize]
            self._blockMin.append(min(block))
            self._blockMax.append(max(block))

    def _extrema(self, start, end):
        """Inclusive zero baseline plus extrema over a half-open sample interval."""
        size = self._blockSize
        first = (start + size - 1) // size
        last = end // size
        if first >= last:
            values = self._samples[start:end]
            return min(0., min(values)), max(0., max(values))
        left = self._samples[start:first * size]
        right = self._samples[last * size:end]
        return (min(0., min(left, default=0.), min(right, default=0.), min(self._blockMin[first:last])),
                max(0., max(left, default=0.), max(right, default=0.), max(self._blockMax[first:last])))

    def _rebuildBars(self):
        self._bars = []
        if not self._samples:
            return
        rect = QRectF(self.contentsRect())
        width = rect.width() - self._barWidth
        height = max(0., rect.height() - self._barWidth)
        if width < 0 or height <= 0:
            return
        stride = self._barWidth + self._barSpacing
        count = max(1, int(width // stride) + 1)
        count = min(count, len(self._samples))
        step = width / (count - 1) if count > 1 else 0
        for i in range(count):
            start = i * len(self._samples) // count
            end = (i + 1) * len(self._samples) // count
            low, high = self._extrema(start, end)
            low = max(-1., low * self._amplitudeScale)
            high = min(1., high * self._amplitudeScale)
            x = rect.left() + self._barWidth / 2 + i * step if count > 1 else rect.center().x()
            cy = rect.center().y()
            # Tiny nonzero segments retain round-cap dots for silence on all Qt backends.
            self._bars.append(QLineF(x, cy - high * height / 2 - .005,
                                     x, cy - low * height / 2 + .005))

    @staticmethod
    def _positive(value, name, allowZero=False):
        value = float(value)
        if not isfinite(value) or (value < 0 if allowZero else value <= 0):
            raise ValueError(f'{name} must be finite and {"nonnegative" if allowZero else "positive"}')
        return value

    def barWidth(self):
        return self._barWidth

    def setBarWidth(self, width):
        self._barWidth = self._positive(width, 'barWidth')
        self._rebuildBars()
        self.update()

    def barSpacing(self):
        return self._barSpacing

    def setBarSpacing(self, spacing):
        self._barSpacing = self._positive(spacing, 'barSpacing', True)
        self._rebuildBars()
        self.update()

    def amplitudeScale(self):
        return self._amplitudeScale

    def setAmplitudeScale(self, scale):
        self._amplitudeScale = self._positive(scale, 'amplitudeScale')
        self._rebuildBars()
        self.update()

    def _setColors(self, light, dark, prefix):
        light, dark = QColor(light), QColor(light if dark is None else dark)
        if not light.isValid() or not dark.isValid():
            raise ValueError('Invalid waveform color')
        setattr(self, '_light' + prefix, light)
        setattr(self, '_dark' + prefix, dark)
        self.update()

    def setWaveformColor(self, light, dark=None):
        self._setColors(light, dark, 'WaveformColor')

    def waveformColor(self):
        return QColor(self._darkWaveformColor if isDarkTheme() else self._lightWaveformColor)

    def setPlayedColor(self, light, dark=None):
        self._setColors(light, dark, 'PlayedColor')

    def playedColor(self):
        return QColor(self._darkPlayedColor if isDarkTheme() else self._lightPlayedColor)

    def setSeekEnabled(self, enabled):
        self._seekEnabled = bool(enabled)
        self._dragging = False
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        self.setFocusPolicy(Qt.StrongFocus if enabled else Qt.NoFocus)

    def isSeekEnabled(self):
        return self._seekEnabled

    def _seek(self, position, force=False):
        previous = self._position
        self.setPosition(position)
        if force or self._position != previous:
            self.seekRequested.emit(self._position)

    def _seekAt(self, x, force=False):
        rect = self.contentsRect()
        fraction = max(0., min(1., (x - rect.left()) / max(1, rect.width() - 1)))
        self._seek(round(fraction * self.duration()), force)

    def mousePressEvent(self, event):
        if self.isEnabled() and self._seekEnabled and self._samples and event.button() == Qt.LeftButton:
            self._dragging = True
            self.setFocus(Qt.MouseFocusReason)
            self._seekAt(event.position().x(), force=True)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.LeftButton:
            self._seekAt(event.position().x())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() == Qt.LeftButton:
            self._seekAt(event.position().x())
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.isEnabled() and self._seekEnabled and self._samples:
            positions = {Qt.Key_Left: self._position - 1000, Qt.Key_Right: self._position + 1000,
                         Qt.Key_Home: 0, Qt.Key_End: self.duration()}
            if event.key() in positions:
                self._seek(positions[event.key()], force=True)
                event.accept()
                return
        super().keyPressEvent(event)

    def sizeHint(self):
        return QSize(480, 160)

    def minimumSizeHint(self):
        return QSize(32, 32)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rebuildBars()

    def paintEvent(self, event):
        if not self._bars:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(.43)
        pen = QPen(self.waveformColor(), self._barWidth, Qt.SolidLine, Qt.RoundCap)
        rect = QRectF(self.contentsRect())
        fraction = self._position / self.duration() if self.duration() else 0
        # Disjoint clips avoid double-compositing the antialiased round caps.
        painter.save()
        if fraction:
            painter.setClipRect(QRectF(rect.left() + rect.width() * fraction, rect.top(),
                                      rect.width() * (1 - fraction), rect.height()))
        painter.setPen(pen)
        painter.drawLines(self._bars)
        painter.restore()
        if fraction:
            painter.setClipRect(QRectF(rect.left(), rect.top(), rect.width() * fraction, rect.height()))
            pen.setColor(self.playedColor())
            painter.setPen(pen)
            painter.drawLines(self._bars)
