"""Text watermark preview plus real controls to demonstrate event pass-through."""

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import (
    BodyLabel, CardWidget, CheckBox, DoubleSpinBox, LineEdit, PushButton,
    ScrollArea, SpinBox, Watermark, getFont, toggleTheme,
)
from qfluentwidgets_pro.common.config import qconfig
from qfluentwidgets_pro.common.style_sheet import isDarkTheme


class WatermarkDemo(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('watermarkInterface')
        self.setWidgetResizable(True)
        self._clicks = 0
        page = QWidget()
        page.setObjectName('watermarkDemoContent')
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(16)
        header = QHBoxLayout()
        header.addWidget(BodyLabel('Watermark — 文本水印', page))
        header.addStretch()
        self.visibleCheckBox = CheckBox('显示水印', page)
        self.visibleCheckBox.setChecked(True)
        header.addWidget(self.visibleCheckBox)
        theme = PushButton('切换主题', page)
        theme.clicked.connect(toggleTheme)
        header.addWidget(theme)
        layout.addLayout(header)
        self.textEdit = LineEdit(page)
        self.textEdit.setText('QFluentWidgets')
        self.textEdit.setPlaceholderText('输入水印内容，例如：内部资料 · 张三 · 工号 1001')
        layout.addWidget(self.textEdit)
        controls = QGridLayout()
        self.angleBox = DoubleSpinBox(page)
        self.angleBox.setRange(-180, 180)
        self.angleBox.setValue(-15)
        self.angleBox.setSuffix('°')
        self.opacityBox = DoubleSpinBox(page)
        self.opacityBox.setRange(0, 1)
        self.opacityBox.setSingleStep(.02)
        self.opacityBox.setValue(.1)
        self.fontBox = SpinBox(page)
        self.fontBox.setRange(8, 80)
        self.fontBox.setValue(18)
        self.horizontalBox = SpinBox(page)
        self.verticalBox = SpinBox(page)
        for box, value in ((self.horizontalBox, 60), (self.verticalBox, 30)):
            box.setRange(0, 500)
            box.setValue(value)
        for i, (label, widget) in enumerate((('角度', self.angleBox), ('透明度', self.opacityBox),
                                             ('字号', self.fontBox), ('横向间距', self.horizontalBox),
                                             ('纵向间距', self.verticalBox))):
            controls.addWidget(BodyLabel(label, page), (i // 3) * 2, i % 3)
            controls.addWidget(widget, (i // 3) * 2 + 1, i % 3)
        layout.addLayout(controls)
        layout.addWidget(BodyLabel('文本水印：不占布局空间，窗口变大后自动铺满。', page))
        self.preview = CardWidget(page)
        self.preview.setMinimumHeight(220)
        layout.addWidget(self.preview)
        layout.addWidget(BodyLabel('覆盖真实内容：下面的输入框和按钮仍可正常操作。', page))
        self.contentCard = CardWidget(page)
        content = QVBoxLayout(self.contentCard)
        content.setContentsMargins(20, 20, 20, 20)
        content.addWidget(BodyLabel('内部资料预览', self.contentCard))
        self.contentEdit = LineEdit(self.contentCard)
        self.contentEdit.setPlaceholderText('试着在水印下面输入文字……')
        content.addWidget(self.contentEdit)
        self.clickButton = PushButton('点我验证点击穿透', self.contentCard)
        content.addWidget(self.clickButton)
        self.clickStatus = BodyLabel('尚未点击', self.contentCard)
        content.addWidget(self.clickStatus)
        content.addStretch()
        self.contentCard.setMinimumHeight(220)
        layout.addWidget(self.contentCard)
        layout.addWidget(BodyLabel('水印只是视觉标识，不修改原始数据，也不能阻止复制或截屏。', page))
        layout.addStretch()
        self.watermarks = [Watermark(self.textEdit.text(), self.preview),
                           Watermark(self.textEdit.text(), self.contentCard)]
        self.textEdit.textChanged.connect(lambda text: self._configure('setText', text))
        self.angleBox.valueChanged.connect(lambda value: self._configure('setAngle', value))
        self.opacityBox.valueChanged.connect(lambda value: self._configure('setOpacity', value))
        self.fontBox.valueChanged.connect(lambda value: self._configure('setFont', getFont(value)))
        self.horizontalBox.valueChanged.connect(self._spacingChanged)
        self.verticalBox.valueChanged.connect(self._spacingChanged)
        self.visibleCheckBox.toggled.connect(lambda visible: self._configure('setVisible', visible))
        self.clickButton.clicked.connect(self._clicked)
        self.setWidget(page)
        qconfig.themeChangedFinished.connect(self._applyTheme)
        self._applyTheme()

    def _configure(self, method, *args):
        for watermark in self.watermarks:
            getattr(watermark, method)(*args)

    def _spacingChanged(self, *_):
        self._configure('setSpacing', self.horizontalBox.value(), self.verticalBox.value())

    def _clicked(self):
        self._clicks += 1
        self.clickStatus.setText(f'点击成功：{self._clicks} 次，水印没有拦截鼠标事件。')

    def _applyTheme(self):
        background = '#262626' if isDarkTheme() else '#f3f3f3'
        self.setStyleSheet('QScrollArea#watermarkInterface { background: %s; border: none; }' % background)
        self.widget().setStyleSheet('QWidget#watermarkDemoContent { background: %s; }' % background)
