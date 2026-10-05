"""Inspect native WebEngine frame buffers, not just ECharts' JS state.

Run with: py -3.9 tests/check_chart_frames.py
Add --without-frame-gate to reproduce the stale-frame regression.
"""

import sys
from time import perf_counter

sys.argv.append('--native')
from check_chart_widget import javascript, wait_for

from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget

from qfluentwidgets_pro.components.widgets.chart_widget import ChartWidget
from qfluentwidgets_pro import Theme, setTheme


def red_fraction(image):
    if image.isNull():
        return 0
    samples = 0
    red = 0
    for y in range(0, image.height(), 8):
        for x in range(0, image.width(), 8):
            c = image.pixelColor(x, y)
            samples += 1
            red += c.red() > 180 and c.green() < 80 and c.blue() < 80
    return red / samples


def run():
    app = QApplication([])
    assert app.platformName() == 'windows'
    stack = QStackedWidget()
    widget = ChartWidget(stack)
    if '--without-frame-gate' in sys.argv:
        widget._frameGate.prepare = widget._frameGate._finish
    other = QWidget(stack)
    stack.addWidget(widget)
    stack.addWidget(other)
    stack.resize(640, 480)
    widget.setOption({
        'animationDuration': 2000, 'animationEasing': 'linear',
        'grid': {'left': 0, 'right': 0, 'top': 0, 'bottom': 0},
        'xAxis': {'type': 'category', 'data': ['A'], 'show': False},
        'yAxis': {'min': 0, 'max': 100, 'show': False},
        'series': [{'type': 'bar', 'data': [100], 'barWidth': '100%',
                    'itemStyle': {'color': '#ff0000'}}],
    })
    stack.show()
    wait_for(lambda: widget._initialized, 'Page not initialized')
    wait_for(lambda: javascript(widget, '!!chart && chart.getZr().animation.isFinished()'),
             'Animation not finished')
    QTest.qWait(200)
    surface = widget._browser.findChild(QQuickWidget)
    assert surface is not None
    page = widget._browser.page()
    for hidden_ms, busy in ((500, False), (0, False), (16, False), (100, False), (0, True)):
        wait_for(lambda: javascript(widget, 'chart.getZr().animation.isFinished()'),
                 'Animation not finished')
        QTest.qWait(100)
        wait_for(lambda: not widget._frameGate.pending, 'Frame gate did not finish')
        final = red_fraction(surface.grabFramebuffer())
        assert final > .8, 'Test chart must fill the surface with red'
        chart_id = javascript(widget, 'chart.id')
        if busy:
            # Keep Chromium busy while Qt switches pages: a JS acknowledgement
            # must not be mistaken for a newly presented frame.
            page.runJavaScript('var until = performance.now() + 180; while (performance.now() < until) {}')
        stack.setCurrentWidget(other)
        if hidden_ms == 100:
            setTheme(Theme.DARK)
        if hidden_ms:
            QTest.qWait(hidden_ms)
        start = perf_counter()
        stack.setCurrentWidget(widget)
        frames = []
        while perf_counter() - start < .35:
            elapsed = (perf_counter() - start) * 1000
            presented = widget.grab().toImage()
            frames.append((round(elapsed, 1), round(red_fraction(presented), 3)))
            assert presented.pixelColor(presented.width() // 2, presented.height() // 2).rgb() != widget._frameGate.marker.rgb(), 'Private frame marker leaked through the cover'
            QTest.qWait(5)
        print('Hidden %d ms, busy=%s; entry frames (ms, red fraction):' % (hidden_ms, busy), frames, flush=True)
        assert not any(red > .8 for _, red in frames), 'Cached completed frame flashed on entry'
        wait_for(lambda: not widget._frameGate.pending, 'Frame gate did not finish')
        assert widget._browser.page() is page
        if hidden_ms != 100:
            assert javascript(widget, 'chart.id') == chart_id
    wait_for(lambda: javascript(widget, 'chart.getZr().animation.isFinished()'),
             'Last replay did not finish')
    QTest.qWait(100)
    assert red_fraction(widget.grab().toImage()) > .8, 'Cover remained over the finished chart'
    stack.close()
    assert not any(red > .8 for _, red in frames), 'Cached completed frame flashed on entry'
    print('PASS: no completed frame in first 350 ms', flush=True)


if __name__ == '__main__':
    run()
