# ChartWidget 依赖 QtWebEngine，刻意不从顶层导出（防 nuitka 误打包）；
# 示例按需直接子模块导入
from qfluentwidgets_pro.components.widgets.chart_widget import ChartWidget

from ..gallery_interface import GalleryInterface


class ChartCard(GalleryInterface):
    """"""

    def __init__(self, title, object_name, option, parent=None):
        super().__init__(
            title=title,
            subtitle="qfluentwidgets_pro.components.chart_widget",
            parent=parent,
        )
        self.setObjectName(object_name)

        chart = ChartWidget(self.view)
        chart.setFixedHeight(550)

        if isinstance(option, str):
            chart.setOptionJS(option)
        else:
            chart.setOption(option)

        self.vBoxLayout.addWidget(chart)

        self.enableTransparentBackground()
