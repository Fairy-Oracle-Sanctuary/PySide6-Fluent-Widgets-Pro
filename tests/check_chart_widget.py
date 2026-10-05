"""Real WebEngine regression check: py -3.9 tests/check_chart_widget.py."""

import json
import os
import sys
from pathlib import Path
from time import perf_counter

if "--native" not in sys.argv:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    # Use software rendering for this headless check only.
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEventLoop, QSize, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from qfluentwidgets_pro import Theme, setTheme
from qfluentwidgets_pro.components.widgets.chart_widget import ChartWidget


def javascript(widget, expression):
    loop = QEventLoop()
    result = []
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)

    def receive(value):
        result.append(value)
        loop.quit()

    widget._browser.page().runJavaScript("JSON.stringify(" + expression + ")", receive)
    timeout.start(5000)
    loop.exec()
    timeout.stop()
    assert result, "JavaScript callback timed out"
    return json.loads(result[0]) if result[0] else None


def wait_for(predicate, message):
    deadline = perf_counter() + 10
    while perf_counter() < deadline:
        if predicate():
            return
        QTest.qWait(20)
    raise AssertionError(message)


def option(value):
    return {
        "animationDuration": 1000,
        "xAxis": {"data": ["A", "B"]},
        "yAxis": {},
        "series": [{"type": "bar", "data": [value, 10]}],
    }


def run():
    app = QApplication.instance() or QApplication([])
    setTheme(Theme.LIGHT)
    started = perf_counter()
    widgets = [ChartWidget() for _ in range(13)]
    print("13 widgets constructed in %.1f ms" % ((perf_counter() - started) * 1000))
    assert all(w._browser is not None and not w._page_requested for w in widgets)
    # Let hidden bootstrap documents finish; none is an initialized chart.
    QTest.qWait(200)
    assert not any(w._initialized for w in widgets)
    for widget in widgets:
        widget.setOption(option(1))

    widget = widgets[0]
    widget.resize(QSize(600, 400))
    widget.setOption(option(2))
    widget.show()
    loads = []
    widget._browser.loadFinished.connect(loads.append)
    wait_for(lambda: widget._initialized, "Chart page failed to load")
    wait_for(lambda: javascript(widget, "!!chart && !!chart.getOption().series"), "No first chart")
    print("First chart rendered in %.1f ms" % ((perf_counter() - started) * 1000))
    assert sum(w._page_requested for w in widgets) == 1
    assert javascript(widget, "chart.getOption().series[0].data[0]") == 2
    first_id = javascript(widget, "chart.id")

    javascript(widget, """(function () {
        window.checkClears = 0;
        var original = chart.clear;
        chart.clear = function () { checkClears++; return original.apply(this, arguments); };
        return true;
    })()""")
    # A page-entry replay should clear the existing instance, without reloading.
    wait_for(lambda: javascript(widget, "chart.getZr().animation.isFinished()"), "Initial animation stuck")
    widget.hide()
    wait_for(lambda: javascript(widget, "replayPrepared && checkClears === 1"),
             "Replay was not prepared while hidden")
    assert javascript(widget, "(chart.getOption().series || []).length") == 0
    assert javascript(widget, "currentOption.series[0].data[0]") == 2
    widget.show()
    wait_for(lambda: javascript(widget, "!replayPrepared && chart.getOption().series.length > 0"),
             "Page entry did not replay")
    assert javascript(widget, "checkClears") == 1
    assert javascript(widget, "chart.id") == first_id
    assert not javascript(widget, "chart.getZr().animation.isFinished()")
    assert loads == [True]

    widget.setAnimationEnabled(False)
    for value in range(3, 12):
        widget.setOption(option(value))
    wait_for(lambda: javascript(widget, "chart.getOption().series[0].data[0] === 11"), "Latest data missing")
    assert javascript(widget, "chart.id") == first_id
    assert javascript(widget, "checkClears") == 1
    assert javascript(widget, "chart.getOption().animation") is False

    # JS callbacks and generated data survive page re-entry without re-evaluation.
    widget.setOptionJS("""
        window.checkEvaluations = (window.checkEvaluations || 0) + 1;
        option = {xAxis: {data: ['A']}, yAxis: {},
            tooltip: {formatter: function () { return 'callback'; }},
            series: [{type: 'bar', data: [42]}]};
    """)
    wait_for(lambda: javascript(widget, "window.checkEvaluations === 1"), "JS option did not run")
    widget.hide()
    widget.show()
    wait_for(lambda: javascript(widget, "checkClears === 2 && !replayPrepared"), "JS chart did not replay")
    assert javascript(widget, "checkEvaluations") == 1
    assert javascript(widget, "chart.getOption().tooltip[0].formatter()") == "callback"

    # Hidden updates remain pending; theme changes are applied on next entry.
    widget.hide()
    widget.setOption(option(90))
    widget.setOption(option(99))
    setTheme(Theme.DARK)
    QTest.qWait(30)
    assert javascript(widget, "chart.id") == first_id
    widget.show()
    wait_for(lambda: javascript(widget, "chart.getOption().series[0].data[0] === 99"), "Hidden update lost")
    assert javascript(widget, "currentTheme") == "dark"
    assert javascript(widget, "chart.getOption().backgroundColor") == "#202020"
    assert javascript(widget, "chart.id") != first_id

    widget.resize(700, 450)
    wait_for(lambda: javascript(widget, "chart.getWidth() === 670"), "Chart did not resize")
    widget.setOption(option(100))
    widget.clear()
    QTest.qWait(50)
    widget.hide()
    widget.show()
    QTest.qWait(50)
    assert javascript(widget, "currentOption === null && (chart.getOption().series || []).length === 0")
    assert loads == [True]
    for item in widgets:
        item.close()
    print("PASS: lazy load, replay, instance reuse, JS callbacks, hidden updates, theme, resize, clear")


if __name__ == "__main__":
    run()
