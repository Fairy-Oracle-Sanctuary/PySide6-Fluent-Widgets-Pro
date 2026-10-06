"""Optional QtMultimedia adapter. Import explicitly; never re-export from __init__."""
import os
from array import array
from math import isfinite

from PySide6.QtCore import QCoreApplication, QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioDecoder, QAudioFormat


class AudioDecoder(QObject):
    """Asynchronously decode an audio file into normalized waveform samples.

    samplesReady emits an independent (float array, sample rate) for each chunk;
    decoded emits the complete recording, followed by finished. Stereo/multichannel
    frames retain the channel with greatest absolute amplitude, avoiding phase
    cancellation. This is visualization data, not a playback downmix. Supported
    file formats depend on the installed Qt multimedia backend/codecs.
    """

    samplesReady = Signal(object, int)
    decoded = Signal(object, int)
    finished = Signal()
    errorOccurred = Signal(str)
    decodingChanged = Signal(bool)
    durationChanged = Signal(int)
    sampleRateChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._decoder = None
        self._samples = array('f')
        self._sampleRate = 0
        self._duration = 0
        self._source = QUrl()
        self._running = False

    def decode(self, source):
        """Start a new file/URL, cancelling any earlier request and its callbacks."""
        if isinstance(source, QUrl):
            url = QUrl(source)
        else:
            path = os.fspath(source)
            if not path:
                raise ValueError('Audio source must not be empty')
            url = QUrl.fromLocalFile(os.path.abspath(path))
        if not url.isValid() or url.isEmpty():
            raise ValueError('Invalid audio source')
        self.stop()
        self._samples = array('f')
        self._setSampleRate(0)
        self._setDuration(0)
        self._source = url
        decoder = QAudioDecoder(self)
        self._decoder = decoder
        decoder.bufferReady.connect(lambda: self._readBuffers(decoder))
        decoder.durationChanged.connect(lambda value: self._onDuration(decoder, value))
        decoder.finished.connect(lambda: self._onFinished(decoder))
        decoder.error.connect(lambda error: self._onError(decoder, error))
        if not decoder.isSupported():
            self._fail(decoder, self.tr('Audio decoding is not supported by this Qt multimedia backend'))
            return
        self._setRunning(True)
        decoder.setSource(url)
        if decoder is self._decoder:
            decoder.start()

    def stop(self):
        """Cancel without emitting decoded/finished. Partial samples remain readable."""
        decoder, self._decoder = self._decoder, None
        if decoder is not None:
            decoder.blockSignals(True)
            decoder.stop()
            decoder.deleteLater()
        self._setRunning(False)

    def isDecoding(self):
        return self._running

    def source(self):
        return QUrl(self._source)

    def samples(self):
        return array('f', self._samples)

    def sampleRate(self):
        return self._sampleRate

    def duration(self):
        return self._duration

    def _setRunning(self, running):
        if running != self._running:
            self._running = running
            self.decodingChanged.emit(running)

    def _setSampleRate(self, rate):
        if rate != self._sampleRate:
            self._sampleRate = rate
            self.sampleRateChanged.emit(rate)

    def _setDuration(self, duration):
        duration = max(0, int(duration))
        if duration != self._duration:
            self._duration = duration
            self.durationChanged.emit(duration)

    @staticmethod
    def samplesFromBuffer(buffer):
        """Copy Qt's native-endian PCM before its QAudioBuffer goes out of scope."""
        if not buffer.isValid():
            raise ValueError(QCoreApplication.translate('AudioDecoder', 'Invalid audio buffer'))
        format = buffer.format()
        channels, rate = format.channelCount(), format.sampleRate()
        types = {QAudioFormat.UInt8: ('B', 128.), QAudioFormat.Int16: ('h', 32768.),
                 QAudioFormat.Int32: ('i', 2147483648.), QAudioFormat.Float: ('f', 1.)}
        if channels <= 0 or rate <= 0 or format.sampleFormat() not in types:
            raise ValueError(QCoreApplication.translate('AudioDecoder', 'Unsupported PCM sample format'))
        code, divisor = types[format.sampleFormat()]
        raw = array(code)
        raw.frombytes(bytes(buffer.constData())[:buffer.byteCount()])
        if len(raw) % channels:
            raise ValueError(QCoreApplication.translate('AudioDecoder', 'Incomplete PCM audio frame'))
        if code == 'B':
            normalized = ((v - 128.) / divisor for v in raw)
        else:
            normalized = (v / divisor for v in raw)
        values = array('f', (max(-1., min(1., v)) if isfinite(v) else 0. for v in normalized))
        if channels == 1:
            return values, rate
        mono = array('f')
        for offset in range(0, len(values), channels):
            mono.append(max(values[offset:offset + channels], key=abs))
        return mono, rate

    def _readBuffers(self, decoder):
        while decoder is self._decoder and decoder.bufferAvailable():
            try:
                samples, rate = self.samplesFromBuffer(decoder.read())
            except (ValueError, TypeError, OverflowError) as error:
                self._fail(decoder, str(error))
                return
            if self._sampleRate and rate != self._sampleRate:
                self._fail(decoder, self.tr('Audio sample rate changed during decoding'))
                return
            self._setSampleRate(rate)
            if decoder is not self._decoder:
                return
            self._samples.extend(samples)
            self.samplesReady.emit(samples, rate)

    def _onDuration(self, decoder, value):
        if decoder is self._decoder:
            self._setDuration(value)

    def _onFinished(self, decoder):
        if decoder is not self._decoder:
            return
        self._readBuffers(decoder)
        if decoder is not self._decoder:
            return
        if not self._samples:
            self._fail(decoder, self.tr('Audio contains no decoded samples'))
            return
        samples, rate = self.samples(), self._sampleRate
        self._setDuration((len(samples) * 1000 + rate - 1) // rate)
        if decoder is not self._decoder:
            return
        self.stop()
        self.decoded.emit(samples, rate)
        self.finished.emit()

    def _onError(self, decoder, error):
        if decoder is self._decoder and error != QAudioDecoder.NoError:
            self._fail(decoder, decoder.errorString() or self.tr('Audio decoding failed'))

    def _fail(self, decoder, message):
        if decoder is self._decoder:
            self.stop()
            self.errorOccurred.emit(message)
