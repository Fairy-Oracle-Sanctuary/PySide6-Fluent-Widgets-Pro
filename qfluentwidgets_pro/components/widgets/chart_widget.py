"""ECharts chart widget with on-demand loading and page-entry animation."""

import json

from PySide6.QtCore import QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from ...common.config import isDarkTheme, qconfig
from ...qframelesswindow.webengine import FramelessWebEngineView
from .card_widget import SimpleCardWidget


class _ChartFrameGate(QWidget):
    """Keep Chromium's stale texture covered until a fresh blank frame arrives.

    JS callbacks/rAF only acknowledge renderer work, not Qt's compositor frame.
    A temporary solid-color frame, behind this opaque widget, fences the two
    pipelines. The next confirmed background frame is safe to reveal. No
    time-based reveal, page reload, or scene-graph/context destruction is used.
    """

    ready = Signal()

    def __init__(self, browser, parent):
        super().__init__(parent)
        self.browser = browser
        self.pending = False
        self.phase = None
        self.serial = 0
        self.background = QColor()
        self.marker = QColor()
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._checkFrame)
        self.hide()

    def arm(self, background):
        self.cancel()
        self.pending = True
        self.background = QColor(background)
        self.update()
        self.setGeometry(self.browser.geometry())
        self.show()
        self.raise_()

    def paintEvent(self, event):
        # Parent QSS may make QWidget backgrounds transparent. The frame fence
        # must remain opaque regardless of inherited gallery styles.
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.background)

    def prepare(self):
        if not self.pending or self.phase is not None:
            return
        # The offscreen test backend does not present Chromium GPU textures.
        # Native frame correctness is exercised separately on Windows.
        if QApplication.platformName() == 'offscreen':
            self._finish()
            return
        self.serial += 1
        self.marker = QColor(17 + self.serial % 200, 31 + (self.serial // 200) % 190, 197)
        self.phase = 'marker'
        self.browser.page().runJavaScript('prepareChartFrame(%s, %s);' % (
            json.dumps(self.marker.name()), json.dumps(self.background.name())))
        self.timer.start()

    def _checkFrame(self):
        surface = self.browser.findChild(QQuickWidget)
        if surface is None or not surface.isVisible():
            return
        frame = surface.grabFramebuffer()
        if frame.isNull():
            return
        expected = self.marker if self.phase == 'marker' else self.background
        # Check the real Qt presentation texture, not canvas pixels read in JS.
        for y in (0, frame.height() // 2, frame.height() - 1):
            for x in (0, frame.width() // 2, frame.width() - 1):
                if frame.pixelColor(x, y).rgb() != expected.rgb():
                    return
        if self.phase == 'marker':
            self.phase = 'background'
            self.browser.page().runJavaScript('releaseChartFrame();')
        else:
            self._finish()

    def _finish(self):
        self.cancel()
        self.ready.emit()

    def cancel(self):
        self.timer.stop()
        self.pending = False
        self.phase = None
        self.hide()


class ChartWidget(SimpleCardWidget):
    """ECharts chart widget with automatic theme switching.

    Construct this widget before showing its top-level window so the frameless
    web view can configure the native window before Mica is applied.
    The web page is loaded on first display. Showing the widget again replays
    the entry animation on the existing chart; data updates reuse that chart.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._option = {}
        self._js_option = ""
        self._initialized = False
        self._pending_option = False
        self._replay_pending = False
        self._animation_enabled = True
        self._page_requested = False

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(15, 15, 15, 15)
        self._renderTimer = QTimer(self)
        self._renderTimer.setSingleShot(True)
        self._renderTimer.timeout.connect(self._doUpdateChart)
        # WebEngine's native-window setup must happen before the host is shown.
        # Only the ECharts document (not the native view) is created lazily.
        self._browser = FramelessWebEngineView(self)
        self._browser.page().setBackgroundColor(self._normalBackgroundColor())
        self._layout.addWidget(self._browser)
        self._browser.loadFinished.connect(self._onLoadFinished)
        self._frameGate = _ChartFrameGate(self._browser, self)
        self._frameGate.ready.connect(self._doUpdateChart)
        qconfig.themeChanged.connect(self._onThemeChanged)

    def _normalBackgroundColor(self):
        return QColor(self._getTheme()[1])

    def _hoverBackgroundColor(self):
        return self._normalBackgroundColor()

    def _pressedBackgroundColor(self):
        return self._normalBackgroundColor()

    def setOption(self, option: dict):
        """Set the complete ECharts option using a Python dictionary."""
        self._option = option
        self._js_option = ""
        self._pending_option = True
        self._updateChart()

    def setOptionJS(self, js_option: str):
        """Set JavaScript that assigns an option, e.g. option = {...};"""
        self._js_option = js_option
        self._option = {}
        self._pending_option = True
        self._updateChart()

    def setAnimationEnabled(self, enabled: bool):
        """Enable animation, or disable it for real-time data updates."""
        self._animation_enabled = enabled
        self._updateChart()

    def clear(self):
        """Clear both the visible chart and its saved option."""
        self._option = {}
        self._js_option = ""
        self._pending_option = False
        self._replay_pending = False
        self._renderTimer.stop()
        if self._initialized:
            self._browser.page().runJavaScript("clearChart();")

    def resize(self, *args):
        """Resize the widget, or fit the chart to its container with no args."""
        if args:
            return super().resize(*args)
        if self._initialized:
            self._browser.page().runJavaScript("scheduleResize();")

    def sizeHint(self) -> QSize:
        return QSize(400, 300)

    def _getTheme(self) -> tuple:
        return ("dark", "#202020") if isDarkTheme() else (None, "#f3f3f3")

    def _initChart(self):
        if self._page_requested:
            return
        self._page_requested = True
        # Load the library separately, avoiding a copy of its 1 MB source in
        # each HTML data URL and allowing Chromium to cache the script.
        self._browser.setUrl(QUrl("qrc:/qfluentwidgets/js/chart.html"))

    def _onLoadFinished(self, success):
        # FramelessWebEngineView bootstraps with a blank document; it is not
        # the chart and must never trigger calls to the ECharts bridge.
        if not self._page_requested or self._browser.url() != QUrl("qrc:/qfluentwidgets/js/chart.html"):
            return
        self._initialized = success
        if success:
            if self._frameGate.pending:
                self._frameGate.prepare()
            else:
                self._updateChart()

    def _onThemeChanged(self):
        self.update()
        if self.isVisible():
            self._browser.page().setBackgroundColor(self._normalBackgroundColor())
            if self._frameGate.pending:
                self._frameGate.arm(self._normalBackgroundColor())
                if self._initialized:
                    self._frameGate.prepare()
        self._updateChart()

    def _updateChart(self):
        if self._initialized and self.isVisible():
            # Coalesce options/theme/show events in the current event-loop turn.
            self._renderTimer.start(0)

    def _doUpdateChart(self):
        if not self._initialized or not self.isVisible() or self._frameGate.pending:
            return

        background_color = self._normalBackgroundColor()
        if self._browser.page().backgroundColor() != background_color:
            self._browser.page().setBackgroundColor(background_color)

        source = None
        if self._pending_option:
            source = self._js_option or (
                "option = " + json.dumps(self._option, ensure_ascii=False) + ";"
            )
        theme, background = self._getTheme()
        arguments = json.dumps(
            [source, theme, background, self._animation_enabled, self._replay_pending],
            ensure_ascii=False,
        )
        self._browser.page().runJavaScript("updateChart.apply(null, " + arguments + ");")
        self._pending_option = False
        self._replay_pending = False

    def showEvent(self, event):
        super().showEvent(event)
        self._layout.activate()
        self._frameGate.arm(self._normalBackgroundColor())
        self._replay_pending = True
        self._initChart()
        self._renderTimer.stop()
        if self._initialized:
            self._frameGate.prepare()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_frameGate'):
            self._layout.activate()
            self._frameGate.setGeometry(self._browser.geometry())

    def hideEvent(self, event):
        self._renderTimer.stop()
        self._frameGate.cancel()
        if self._initialized:
            self._browser.page().runJavaScript("hideChart();")
        super().hideEvent(event)
