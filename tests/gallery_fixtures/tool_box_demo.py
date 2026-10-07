"""Exclusive native tool panels matching the blend/hue/sharpen toolbox example."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import (
    BodyLabel, ComboBox, PrimaryPushButton, PushButton, ScrollArea, Slider,
    ToolBox, toggleTheme,
)
from qfluentwidgets_pro.common.config import qconfig
from qfluentwidgets_pro.common.style_sheet import isDarkTheme


class ToolBoxDemo(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('toolBoxInterface')
        self.setWidgetResizable(True)
        page = QWidget()
        page.setObjectName('toolBoxDemoContent')
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(16)
        header = QHBoxLayout()
        header.addWidget(BodyLabel('ToolBox — 工具箱', page))
        header.addStretch()
        theme = PushButton('切换主题', page)
        theme.clicked.connect(toggleTheme)
        header.addWidget(theme)
        layout.addLayout(header)
        self.toolBox = ToolBox(page)
        self.toolBox.setFixedWidth(350)
        self.blendPage = QWidget()
        blend = QVBoxLayout(self.blendPage)
        blend.setContentsMargins(0, 0, 0, 0)
        blend.setSpacing(12)
        blend.addWidget(BodyLabel('混合模式', self.blendPage))
        self.modeBox = ComboBox(self.blendPage)
        self.modeBox.addItems(['正常', '正片叠底', '滤色', '叠加'])
        self.modeBox.setFixedWidth(150)
        blend.addWidget(self.modeBox)
        blend.addWidget(BodyLabel('不透明度', self.blendPage))
        self.opacitySlider = Slider(Qt.Horizontal, self.blendPage)
        self.opacitySlider.setRange(0, 100)
        self.opacitySlider.setValue(30)
        blend.addWidget(self.opacitySlider)
        actions = QHBoxLayout()
        self.applyButton = PrimaryPushButton('应用', self.blendPage)
        self.resetButton = PushButton('重置', self.blendPage)
        actions.addWidget(self.applyButton)
        actions.addWidget(self.resetButton)
        blend.addLayout(actions)
        self.toolBox.addItem(self.blendPage, '混合')
        self.huePage, self.hueSlider = self._sliderPage('色度', -180, 180, 0)
        self.sharpenPage, self.sharpenSlider = self._sliderPage('锐化强度', 0, 100, 20)
        self.toolBox.addItem(self.huePage, '色度')
        self.toolBox.addItem(self.sharpenPage, '锐化')
        layout.addWidget(self.toolBox, 0, Qt.AlignLeft)
        self.status = BodyLabel('每次最多展开一项；点击已展开的标题可全部收起。', page)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()
        self.toolBox.currentChanged.connect(self._currentChanged)
        self.applyButton.clicked.connect(lambda: self.status.setText(
            f'已应用：{self.modeBox.currentText()}，不透明度 {self.opacitySlider.value()}%。'))
        self.resetButton.clicked.connect(self._reset)
        self.setWidget(page)
        qconfig.themeChangedFinished.connect(self._applyTheme)
        self._applyTheme()

    def _sliderPage(self, title, minimum, maximum, value):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(BodyLabel(title, page))
        slider = Slider(Qt.Horizontal, page)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        layout.addWidget(slider)
        return page, slider

    def _currentChanged(self, index):
        self.status.setText('所有工具已收起。' if index < 0 else
                            f'当前展开：{self.toolBox.itemText(index)}；其他工具自动收起，原值保持不变。')

    def _reset(self):
        self.modeBox.setCurrentIndex(0)
        self.opacitySlider.setValue(30)
        self.status.setText('混合参数已重置。')

    def _applyTheme(self):
        background = '#262626' if isDarkTheme() else '#f3f3f3'
        self.setStyleSheet('QScrollArea#toolBoxInterface { background: %s; border: none; }' % background)
        self.widget().setStyleSheet('QWidget#toolBoxDemoContent { background: %s; }' % background)
