# coding:utf-8
"""
ECharts chart widget for PySide6 Fluent Widgets
"""

import json

from PySide6.QtCore import QFile, QSize, QTextStream, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout

from ...common.config import isDarkTheme, qconfig
from ...qframelesswindow.webengine import FramelessWebEngineView
from .card_widget import SimpleCardWidget


class ChartWidget(SimpleCardWidget):
    """ECharts chart widget with theme auto-switch support

    Examples
    --------
    Basic usage:

    chart = ChartWidget()
    chart.setOption({
        "title": {"text": "ECharts Demo"},
        "xAxis": {"data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
        "yAxis": {},
        "series": [{"type": "bar", "data": [120, 200, 150, 80, 70, 110, 130]}]
    })
    """

    # Class-level cache for echarts.js
    _echarts_js_cache = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._option = {}
        self._js_option = ""
        self._initialized = False
        self._pending_option = False
        self._chart_shown = False
        self._animation_enabled = True  # Animation control for real-time updates

        # Create layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(15, 15, 15, 15)

        # Create web view
        self._browser = FramelessWebEngineView(self)
        self._layout.addWidget(self._browser)

        # Connect load finished signal
        self._browser.loadFinished.connect(self._onLoadFinished)

        # Connect theme change signal
        qconfig.themeChanged.connect(self._onThemeChanged)

        # Initialize chart framework
        self._initChart()

    def _normalBackgroundColor(self):
        """Sync card background with chart background"""
        if isDarkTheme():
            return QColor(32, 32, 32)  # #202020
        else:
            return QColor(243, 243, 243)  # #f3f3f3

    def _hoverBackgroundColor(self):
        return self._normalBackgroundColor()

    def _pressedBackgroundColor(self):
        return self._normalBackgroundColor()

    def setOption(self, option: dict):
        """Set ECharts option with Python dict

        Parameters
        ----------
        option : dict
            ECharts option dictionary
        """
        self._option = option
        self._js_option = ""
        self._updateChart()

    def setOptionJS(self, js_option: str):
        """Set ECharts option with JavaScript string

        Parameters
        ----------
        js_option : str
            JavaScript option string, e.g. "option = {...};"
        """
        self._js_option = js_option
        self._option = {}
        self._updateChart()

    def setAnimationEnabled(self, enabled: bool):
        """Enable or disable chart animation

        Parameters
        ----------
        enabled : bool
            Whether to enable animation. Disable for real-time data updates.
        """
        self._animation_enabled = enabled

    def clear(self):
        """Clear the chart"""
        self._option = {}
        self._js_option = ""
        self._browser.page().runJavaScript("if(window.chart) chart.clear();")

    def resize(self):
        """Resize the chart to fit container"""
        self._browser.page().runJavaScript("if(window.chart) chart.resize();")

    def sizeHint(self) -> QSize:
        return QSize(400, 300)

    def _onLoadFinished(self, success):
        """Handle HTML load finished"""
        if success:
            self._initialized = True
            if self.isVisible() and self._pending_option:
                self._chart_shown = True
                self._doUpdateChart()

    def _onThemeChanged(self):
        """Handle theme change"""
        self._applyTheme()

    def _getTheme(self) -> tuple:
        """Get current theme info

        Returns
        -------
        tuple : (theme_name, bg_color)
        """

        if isDarkTheme():
            return ("dark", "#202020")
        else:
            return (None, "#f3f3f3")

    def _loadEChartsJS(self) -> str:
        """Load echarts.min.js from Qt resource (cached)

        Returns
        -------
        str : echarts JavaScript content
        """
        # Use cached content if available
        if ChartWidget._echarts_js_cache is not None:
            return ChartWidget._echarts_js_cache

        file = QFile(":/qfluentwidgets/js/echarts.min.js")
        if not file.open(QFile.ReadOnly | QFile.Text):
            raise RuntimeError("Failed to load echarts.min.js from resource")

        stream = QTextStream(file)
        content = stream.readAll()
        file.close()

        # Cache for future use
        ChartWidget._echarts_js_cache = content
        return content

    def _initChart(self):
        """Initialize chart HTML framework (only once)"""
        theme, bg_color = self._getTheme()
        echarts_js = self._loadEChartsJS()
        theme_str = f"'{theme}'" if theme else "null"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script>{echarts_js}</script>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body, html {{ width: 100%; height: 100%; background-color: {bg_color}; }}
                #container {{ width: 100%; height: 100%; }}
            </style>
        </head>
        <body>
            <div id="container"></div>
            <script>
                var chart = null;
                var currentTheme = {theme_str};
                var currentBgColor = '{bg_color}';

                function initChart(theme, bgColor) {{
                    if (chart) {{
                        chart.dispose();
                    }}
                    currentTheme = theme;
                    currentBgColor = bgColor;
                    document.body.style.backgroundColor = bgColor;
                    chart = echarts.init(document.getElementById('container'), theme);
                    window.chart = chart;
                }}

                function updateChart(optionStr, bgColor) {{
                    if (!chart) {{
                        initChart(currentTheme, bgColor);
                    }}
                    var option;
                    eval(optionStr);
                    if (!option.backgroundColor) {{
                        option.backgroundColor = bgColor;
                    }}
                    chart.setOption(option, {{ notMerge: true }});
                }}

                function applyTheme(theme, bgColor) {{
                    currentBgColor = bgColor;
                    document.body.style.backgroundColor = bgColor;
                    if (chart) {{
                        var currentOption = chart.getOption();
                        chart.dispose();
                        chart = echarts.init(document.getElementById('container'), theme);
                        window.chart = chart;
                        if (currentOption) {{
                            currentOption.backgroundColor = bgColor;
                            chart.setOption(currentOption, {{ notMerge: true }});
                        }}
                    }}
                }}

                window.onresize = function() {{ if(chart) chart.resize(); }};
            </script>
        </body>
        </html>
        """

        self._browser.setHtml(html_content)

    def _updateChart(self):
        """Update chart option via JavaScript (no page reload)"""
        if not self._initialized:
            self._pending_option = True
            return
        self._doUpdateChart()

    def _doUpdateChart(self):
        """Actually execute the chart update"""
        theme, bg_color = self._getTheme()
        theme_str = f"'{theme}'" if theme else "null"

        # Build option string
        if self._js_option:
            option_str = self._js_option
        elif self._option:
            option_str = f"option = {json.dumps(self._option, ensure_ascii=False)};"
        else:
            option_str = "option = {};"

        js_code = f"""
        (function() {{
            if (chart) {{
                chart.dispose();
                chart = null;
            }}
            initChart({theme_str}, '{bg_color}');
            var option;
            {option_str}
            if (!option.backgroundColor) {{
                option.backgroundColor = '{bg_color}';
            }}
            option.animation = {"true" if self._animation_enabled else "false"};
            option.animationDuration = 1000;
            option.animationEasing = 'cubicOut';
            chart.setOption(option, {{ notMerge: true }});
        }})();
        """
        self._browser.page().runJavaScript(js_code)
        self._pending_option = False

    def _applyTheme(self):
        """Apply theme change via JavaScript (no page reload)"""
        if not self._initialized:
            return

        # Re-render chart with new theme to update all colors
        self._doUpdateChart()

        # Update card background
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._browser.page().runJavaScript("if(window.chart) chart.resize();")

    def showEvent(self, e):
        super().showEvent(e)
        if not self._initialized:
            return
        QTimer.singleShot(50, self._delayedRender)

    def _delayedRender(self):
        self._chart_shown = True
        self._doUpdateChart()
