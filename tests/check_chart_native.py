"""Windows/Mica integration: py -3.9 -X faulthandler tests/check_chart_native.py.

Opens a real Gallery window and exercises page navigation without disabling GPU.
"""

import faulthandler
import gc
import sys

faulthandler.enable()
sys.argv.append("--native")
from check_chart_widget import javascript, wait_for

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from main import MainWindow
from qfluentwidgets_pro import Theme, setTheme
from qfluentwidgets_pro.components.widgets.chart_widget import ChartWidget


def run():
    app = QApplication([])
    assert app.platformName() == "windows", "This check needs native Windows Qt"
    host = QWidget()
    # Exercise the actual entry method and its lifetime management.
    MainWindow._openChartWindow(host)
    window = host._chartWindow
    window.setWindowTitle("Chart native regression")
    handle = window.winId()
    flags = window.windowFlags()
    translucent = window.testAttribute(Qt.WA_TranslucentBackground)
    assert translucent, "FramelessWebEngineView did not prepare the Mica host"
    assert window.isMicaEffectEnabled()
    failures = []
    first_chart = window.lineChart.findChild(ChartWidget)
    first_id = None
    pages = [window.lineChart, window.barChart, window.pieChart, window.scatterChart,
             window.klineChart, window.radarChart, window.boxplotChart, window.heatChart,
             window.relationChart, window.funnelChart, window.gaugeChart,
             window.calendarChart, window.realtimeChart, window.lineChart]
    for index, page in enumerate(pages):
        window.switchTo(page)
        chart = page.findChild(ChartWidget)
        wait_for(lambda: chart.isVisible() and chart._initialized, page.objectName())
        chart._browser.page().renderProcessTerminated.connect(
            lambda status, code: failures.append((status, code)))
        wait_for(lambda: javascript(chart, "!!chart && (chart.getOption().series || []).length > 0"),
                 "Chart did not render: " + page.objectName())
        assert window.isVisible(), "Navigation hid the window"
        assert window.winId() == handle, "Navigation recreated the native window"
        assert window.windowFlags() == flags
        assert window.testAttribute(Qt.WA_TranslucentBackground) == translucent
        assert not failures, failures
        if index == 0:
            first_id = javascript(chart, "chart.id")
        print("PASS", page.objectName(), flush=True)

    assert javascript(first_chart, "chart.id") == first_id
    for theme in (Theme.DARK, Theme.LIGHT):
        setTheme(theme)
        QTest.qWait(100)
        assert window.isVisible() and window.isMicaEffectEnabled()

    # Reopening reuses the Python-owned window after a GC and close/show cycle.
    window.close()
    gc.collect()
    MainWindow._openChartWindow(host)
    assert host._chartWindow is window and window.isVisible()
    wait_for(lambda: javascript(first_chart, "!!chart && !renderPending"), "Reopen failed")
    assert not failures, failures
    if "--preview" in sys.argv:
        setTheme(Theme.DARK)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(60000, app.quit)
        app.exec()
    window.close()
    host.close()
    print("PASS: native frame, Mica, 13 pages, replay, themes, renderer, window lifetime", flush=True)


if __name__ == "__main__":
    run()
