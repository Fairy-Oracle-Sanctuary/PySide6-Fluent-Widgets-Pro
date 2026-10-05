"""Waveform extrema/cache, transparent rendering, streaming, progress and seeking."""
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QImage, QMouseEvent, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import AudioWaveformWidget, Theme, setTheme


def render(widget):
    image = QImage(widget.size(), QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    widget.render(painter, QPoint(), renderFlags=widget.RenderFlag.DrawChildren)
    painter.end()
    return image


def run():
    app = QApplication([])
    w = AudioWaveformWidget()
    w.resize(545, 300)
    w.show()
    app.processEvents()
    assert w.sampleCount() == w.duration() == w.position() == 0
    assert not w.autoFillBackground() and not w.toolTip()
    assert render(w).pixelColor(100, 100).alpha() == 0
    durations, positions, seeks = [], [], []
    w.durationChanged.connect(durations.append)
    w.positionChanged.connect(positions.append)
    w.seekRequested.connect(seeks.append)
    rng = random.Random(7)
    data = [rng.uniform(-1, 1) for _ in range(12345)]
    w.setSamples(data, 8000)
    assert w.duration() == 1544 and durations == [1544]
    original = w.samples()
    for _ in range(100):
        start = rng.randrange(len(data))
        end = rng.randrange(start + 1, len(data) + 1)
        low, high = w._extrema(start, end)
        assert low == min(0., min(original[start:end]))
        assert high == max(0., max(original[start:end]))
    copy = w.samples()
    copy[0] = 1
    assert w.samples()[0] == original[0]
    bars = w._bars
    w.setPosition(700)
    assert w._bars is bars and positions == [700] and not seeks
    w.setPosition(999999)
    assert w.position() == w.duration()
    w.setPosition(-1)
    assert w.position() == 0
    # Arbitrary chunk boundaries produce the same cache/geometry as one recording.
    stream = AudioWaveformWidget()
    stream.resize(w.size())
    for start in range(0, len(data), 93):
        stream.appendSamples(data[start:start + 93], 8000)
    assert stream.samples() == original
    assert stream._blockMin == w._blockMin and stream._blockMax == w._blockMax
    assert stream._bars == w._bars
    w.setPosition(500)
    before = w.samples()
    for operation in (lambda: w.appendSamples([0], 24000),
                      lambda: w.setSamples([float('nan')], 8000),
                      lambda: w.appendSamples([float('inf')], 8000),
                      lambda: w.setSamples([0], 0),
                      lambda: w.setSamples([0], 1.5),
                      lambda: w.setSamples([0], True),
                      lambda: w.setBarWidth(0), lambda: w.setBarSpacing(-1),
                      lambda: w.setAmplitudeScale(float('nan')),
                      lambda: w.setWaveformColor('invalid-color')):
        try:
            operation()
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid input accepted')
        assert w.samples() == before and w.position() == 500
    try:
        w.setSamples(b'encoded data')
    except TypeError:
        pass
    else:
        raise AssertionError('Encoded bytes accepted as normalized samples')
    w.appendSamples([0] * 8000)
    assert w.position() == 500 and w.duration() == 2544
    w.setSamples([-2, 2], 24000)
    assert list(w.samples()) == [-1, 1] and w.duration() == 1 and w.position() == 0
    # Silent samples remain center dots; resize preserves peaks and changes bar density.
    w.setSamples([0] * 8000, 8000)
    w.setWaveformColor('#cccccc', '#555555')
    w.setPlayedColor('#222222', '#eeeeee')
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        w.setPosition(500)
        image = render(w)
        for x, expected in ((100, w.playedColor()), (400, w.waveformColor())):
            region = [image.pixelColor(px, py) for px in range(x - 5, x + 6)
                      for py in range(147, 153)]
            opaque = max(region, key=lambda color: color.alpha())
            assert opaque.alpha() > 100 and abs(opaque.red() - expected.red()) <= 2, (theme, x, opaque.getRgb(), expected.getRgb())
        assert image.pixelColor(100, 60).alpha() == 0
        w.setEnabled(False)
        assert max(render(w).pixelColor(x, 150).alpha() for x in range(90, 110)) < 150
        w.setEnabled(True)
    w.setPosition(0)
    QTest.mouseClick(w, Qt.LeftButton, pos=QPoint(272, 150))
    assert w.position() == 500 and seeks == [500]
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(0, 150))
    event = QMouseEvent(QEvent.MouseMove, QPointF(400, 150),
                       QPointF(w.mapToGlobal(QPoint(400, 150))),
                       Qt.NoButton, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(w, event)
    assert w.position() == 735
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(544, 150))
    assert w.position() == 1000 and not w._dragging
    QTest.keyClick(w, Qt.Key_Home)
    assert w.position() == 0
    QTest.keyClick(w, Qt.Key_Right)
    assert w.position() == 1000
    QTest.keyClick(w, Qt.Key_Left)
    assert w.position() == 0
    QTest.keyClick(w, Qt.Key_End)
    assert w.position() == 1000
    w.setSeekEnabled(False)
    count = len(seeks)
    QTest.mouseClick(w, Qt.LeftButton, pos=QPoint(0, 150))
    QTest.keyClick(w, Qt.Key_Home)
    assert w.position() == 1000 and len(seeks) == count
    w.setSamples([0] * 99 + [1] + [0] * 9900, 8000)
    w.resize(100, 64)
    app.processEvents()
    assert len(w._bars) < 40 and min(line.y1() for line in w._bars) < 1
    w.resize(1, 1)
    app.processEvents()
    assert not w._bars
    w.clear()
    assert w.sampleCount() == w.duration() == w.position() == 0
    w.appendSamples([0, .5], 16000)
    assert w.sampleRate() == 16000
    w.close()
    stream.close()
    print('PASS: extrema cache, spike retention, transparent light/dark rendering, silence, clipping, streaming, validation, progress, drag and keyboard seeking')


if __name__ == '__main__':
    run()
