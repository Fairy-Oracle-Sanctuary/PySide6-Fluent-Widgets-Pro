# coding: utf-8
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from qfluentwidgets_pro import (
    FluentWindow,
    NavigationItemPosition,
    SplashScreen,
    toggleTheme,
)
from qfluentwidgets_pro.components.widgets.menu import FIF

from ...common.resource import *
from ...common.translator import Translator
from .charts_interface import ChartCard
from .charts_js import (
    bar_chart,
    boxplot_chart,
    calendar_chart,
    funnel_chart,
    gauge_chart,
    get_relation_chart_option,
    heat_chart,
    kline_chart,
    line_chart,
    pie_chart,
    radar_chart,
    scatter_chart,
)


class ChartMainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()

        self.lineChart = ChartCard(
            "折线图",
            "chartInterface",
            line_chart,
            self,
        )
        self.barChart = ChartCard(
            "柱状图",
            "barInterface",
            bar_chart,
            self,
        )
        self.pieChart = ChartCard(
            "饼图",
            "pieInterface",
            pie_chart,
            self,
        )
        self.scatterChart = ChartCard(
            "散点图",
            "scatterInterface",
            scatter_chart,
            self,
        )
        self.klineChart = ChartCard(
            "K线图",
            "klineInterface",
            kline_chart,
            self,
        )
        self.radarChart = ChartCard(
            "雷达图",
            "radarInterface",
            radar_chart,
            self,
        )

        self.boxplotChart = ChartCard(
            "盒须图",
            "boxplotInterface",
            boxplot_chart,
            self,
        )
        self.heatChart = ChartCard(
            "热力图",
            "heatInterface",
            heat_chart,
            self,
        )
        self.relationChart = ChartCard(
            "关系图",
            "relationInterface",
            get_relation_chart_option(),
            self,
        )
        self.funnelChart = ChartCard(
            "漏斗图",
            "funnelInterface",
            funnel_chart,
            self,
        )
        self.gaugeChart = ChartCard(
            "仪表盘",
            "gaugeInterface",
            gauge_chart,
            self,
        )
        self.calendarChart = ChartCard(
            "日历图",
            "calendarInterface",
            calendar_chart,
            self,
        )

        # add items to navigation interface
        self.initNavigation()
        self.splashScreen.finish()

    def initNavigation(self):
        # add navigation items
        t = Translator()
        self.addSubInterface(self.lineChart, FIF.CLEAR_SELECTION, self.tr("折线图"))
        self.addSubInterface(self.barChart, FIF.ALIGNMENT, self.tr("柱状图"))
        self.addSubInterface(self.pieChart, FIF.PALETTE, self.tr("饼图"))
        self.addSubInterface(self.scatterChart, FIF.MORE, self.tr("散点图"))
        self.addSubInterface(self.klineChart, FIF.FULL_SCREEN, self.tr("K线图"))
        self.addSubInterface(self.radarChart, FIF.GLOBE, self.tr("雷达图"))
        self.addSubInterface(self.boxplotChart, FIF.TILES, self.tr("盒须图"))
        self.addSubInterface(self.heatChart, FIF.BRIGHTNESS, self.tr("热力图"))
        self.addSubInterface(self.relationChart, FIF.IOT, self.tr("关系图"))
        self.addSubInterface(self.funnelChart, FIF.PIE_SINGLE, self.tr("漏斗图"))
        self.addSubInterface(self.gaugeChart, FIF.SPEED_MEDIUM, self.tr("仪表盘"))
        self.addSubInterface(self.calendarChart, FIF.CALENDAR, self.tr("日历图"))

        self.navigationInterface.addItem(
            routeKey="theme",
            icon=FIF.CONSTRACT,
            text=t.changeTheme,
            onClick=toggleTheme,
            selectable=False,
            tooltip=t.changeTheme,
            position=NavigationItemPosition.BOTTOM,
        )

    def initWindow(self):

        self.resize(960, 780)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon(":/gallery/images/logo.png"))
        self.setWindowTitle("PyQt-Fluent-Widgets")

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "splashScreen"):
            self.splashScreen.resize(self.size())
