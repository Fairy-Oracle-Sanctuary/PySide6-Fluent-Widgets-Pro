"""Native PCM conversion and real asynchronous file decoding (QtMultimedia required)."""
import os
import sys
import tempfile
import wave
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QElapsedTimer
from PySide6.QtMultimedia import QAudioBuffer, QAudioFormat
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import AudioWaveformWidget
from qfluentwidgets_pro.common.audio_decoder import AudioDecoder


def wait_until(predicate):
    timer = QElapsedTimer()
    timer.start()
    while not predicate() and timer.elapsed() < 10000:
        QTest.qWait(20)
    assert predicate(), 'Qt decoder timed out'


def make_buffer(code, values, sampleFormat, channels=1):
    format = QAudioFormat()
    format.setSampleRate(8000)
    format.setChannelCount(channels)
    format.setSampleFormat(sampleFormat)
    return QAudioBuffer(array(code, values).tobytes(), format)


def run():
    app = QApplication([])
    for code, raw, format, expected in (
        ('B', [0, 128, 255], QAudioFormat.UInt8, [-1, 0, 127 / 128]),
        ('h', [-32768, 0, 32767], QAudioFormat.Int16, [-1, 0, 32767 / 32768]),
        ('i', [-2147483648, 0, 2147483647], QAudioFormat.Int32, [-1, 0, 1]),
        ('f', [-2, 0, .25, 2, float('nan')], QAudioFormat.Float, [-1, 0, .25, 1, 0]),
    ):
        values, rate = AudioDecoder.samplesFromBuffer(make_buffer(code, raw, format))
        assert rate == 8000 and len(values) == len(expected)
        assert all(abs(a - b) < 1e-6 for a, b in zip(values, expected))
    values, _ = AudioDecoder.samplesFromBuffer(
        make_buffer('h', [16384, -16384, -32768, 2000], QAudioFormat.Int16, 2))
    assert list(values) == [.5, -1]  # preserve anti-phase stereo amplitude
    try:
        AudioDecoder.samplesFromBuffer(QAudioBuffer())
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid buffer accepted')
    assert 'PySide6.QtMultimediaWidgets' not in sys.modules
    decoder = AudioDecoder()
    whole, streamed = AudioWaveformWidget(), AudioWaveformWidget()
    decoder.decoded.connect(whole.setSamples)
    decoder.samplesReady.connect(streamed.appendSamples)
    done, errors, states = [], [], []
    decoder.finished.connect(lambda: done.append(True))
    decoder.errorOccurred.connect(errors.append)
    decoder.decodingChanged.connect(states.append)
    with tempfile.TemporaryDirectory(prefix='codex-waveform-') as temp:
        path = Path(temp) / '音频测试.wav'
        raw = array('h', [16384, -16384] * 2400)
        if sys.byteorder != 'little':
            raw.byteswap()
        with wave.open(str(path), 'wb') as file:
            file.setnchannels(2)
            file.setsampwidth(2)
            file.setframerate(8000)
            file.writeframes(raw.tobytes())
        decoder.decode(path)
        wait_until(lambda: done or errors)
        assert done == [True] and not errors, errors
        assert not decoder.isDecoding() and states == [True, False]
        assert decoder.sampleRate() == 8000 and decoder.duration() == 300
        assert len(decoder.samples()) == 2400
        assert whole.samples() == streamed.samples() == decoder.samples()
        assert all(abs(sample) == .5 for sample in whole.samples())
        assert whole.duration() == 300
        snapshot = whole.samples()
        # Cancel/restart must ignore stale callbacks and not duplicate chunks.
        done.clear()
        streamed.clear()
        decoder.decode(path)
        decoder.stop()
        QTest.qWait(50)
        assert not done and not decoder.isDecoding()
        decoder.decode(path)
        wait_until(lambda: done or errors)
        assert done == [True] and not errors and decoder.samples() == snapshot
        assert streamed.samples() == snapshot
        done.clear()
        decoder.decode(Path(temp) / 'missing.wav')
        wait_until(lambda: errors)
        assert not done and not decoder.isDecoding()
        errors.clear()
        bad = Path(temp) / 'invalid.wav'
        bad.write_bytes(b'not an audio file')
        decoder.decode(bad)
        wait_until(lambda: errors)
        assert not done and not decoder.isDecoding()
        errors.clear()
        done.clear()
        streamed.clear()
        decoder.decode(path)  # recover after failures
        wait_until(lambda: done or errors)
        assert done == [True] and not errors and whole.samples() == snapshot
        for width, pcm in ((1, bytes([0, 128, 255] * 800)),
                           (3, b''.join(value.to_bytes(3, 'little', signed=True)
                                       for value in [-8388608, 0, 8388607] * 800))):
            monoPath = Path(temp) / f'mono-{width * 8}.wav'
            with wave.open(str(monoPath), 'wb') as file:
                file.setnchannels(1)
                file.setsampwidth(width)
                file.setframerate(8000)
                file.writeframes(pcm)
            errors.clear()
            done.clear()
            streamed.clear()
            decoder.decode(monoPath)
            wait_until(lambda: done or errors)
            assert done == [True] and not errors, errors
            assert len(decoder.samples()) == 2400 and decoder.duration() == 300
            assert whole.samples() == streamed.samples()
            assert decoder.samples()[0] == -1. and decoder.samples()[1] == 0.
            assert decoder.samples()[2] > .99
        try:
            decoder.decode('')
        except ValueError:
            pass
        else:
            raise AssertionError('Empty source accepted')
    decoder.stop()
    app.processEvents()
    print('PASS: UInt8/Int16/Int32/float PCM, anti-phase stereo, real 8/16/24-bit WAV decode, streamed/complete results, cancel/restart, error reporting and recovery')


if __name__ == '__main__':
    run()
