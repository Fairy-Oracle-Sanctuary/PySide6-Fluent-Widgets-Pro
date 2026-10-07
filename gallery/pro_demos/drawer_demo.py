"""Four-direction, parent-scoped drawer demo with reusable custom content."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import (
    BodyLabel, CheckBox, Drawer, DrawerPosition, LineEdit, PushButton,
    ScrollArea, SpinBox, toggleTheme,
)
from qfluentwidgets_pro.common.config import qconfig
from qfluentwidgets_pro.common.style_sheet import isDarkTheme


class DrawerDemo(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('drawerInterface')
        self.setWidgetResizable(True)
        page = QWidget()
        page.setObjectName('drawerDemoContent')
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(16)
        header = QHBoxLayout()
        header.addWidget(BodyLabel('Drawer — 四向抽屉', page))
        header.addStretch()
        theme = PushButton('切换主题', page)
        theme.clicked.connect(toggleTheme)
        header.addWidget(theme)
        layout.addLayout(header)
        directions = QHBoxLayout()
        self.directionButtons = {}
        for title, position in (('左侧', DrawerPosition.LEFT), ('右侧', DrawerPosition.RIGHT),
                                ('顶部', DrawerPosition.TOP), ('底部', DrawerPosition.BOTTOM)):
            button = PushButton(title, page)
            button.clicked.connect(lambda checked=False, side=position: self.drawer.open(side))
            self.directionButtons[position] = button
            directions.addWidget(button)
        directions.addStretch()
        layout.addLayout(directions)
        options = QHBoxLayout()
        options.addWidget(BodyLabel('宽度 / 高度', page))
        self.sizeBox = SpinBox(page)
        self.sizeBox.setRange(100, 640)
        self.sizeBox.setValue(320)
        options.addWidget(self.sizeBox)
        self.animateCheckBox = CheckBox('滑动动画', page)
        self.animateCheckBox.setChecked(True)
        options.addWidget(self.animateCheckBox)
        self.maskCheckBox = CheckBox('点击遮罩关闭', page)
        self.maskCheckBox.setChecked(True)
        options.addWidget(self.maskCheckBox)
        options.addStretch()
        layout.addLayout(options)
        layout.addWidget(BodyLabel('抽屉只覆盖下面的内容区域；可按 Esc、点击遮罩或右上角关闭。', page))
        self.host = QWidget(page)
        self.host.setObjectName('drawerDemoHost')
        self.host.setMinimumHeight(460)
        content = QVBoxLayout(self.host)
        content.setContentsMargins(24, 24, 24, 24)
        content.addWidget(BodyLabel('内容区域', self.host))
        self.backgroundEdit = LineEdit(self.host)
        self.backgroundEdit.setPlaceholderText('关闭抽屉后可以继续编辑；原内容保持不变。')
        content.addWidget(self.backgroundEdit)
        content.addStretch()
        content.addWidget(BodyLabel('面板带阴影，窗口缩放时始终贴住所选边缘。', self.host))
        layout.addWidget(self.host, 1)
        self.status = BodyLabel('选择一个方向打开抽屉。', page)
        layout.addWidget(self.status)
        self.drawer = Drawer('标题', self.host)
        self.drawer.viewLayout.addStretch()
        self.emptyLabel = BodyLabel('没有更多通知', self.drawer.contentWidget)
        self.drawer.addWidget(self.emptyLabel, alignment=Qt.AlignCenter)
        self.drawer.viewLayout.addStretch()
        self.sizeBox.valueChanged.connect(self.drawer.setDrawerSize)
        self.animateCheckBox.toggled.connect(lambda enabled: self.drawer.setAnimationDuration(240 if enabled else 0))
        self.maskCheckBox.toggled.connect(self.drawer.setClosableOnMaskClicked)
        self.drawer.opened.connect(lambda: self.status.setText('抽屉已打开，内部内容由应用自行添加。'))
        self.drawer.closed.connect(lambda: self.status.setText('抽屉已关闭，内容不会被删除。'))
        self.setWidget(page)
        qconfig.themeChangedFinished.connect(self._applyTheme)
        self._applyTheme()

    def _applyTheme(self):
        dark = isDarkTheme()
        background = '#262626' if dark else '#f3f3f3'
        self.setStyleSheet('QScrollArea#drawerInterface { background: %s; border: none; }' % background)
        self.widget().setStyleSheet('QWidget#drawerDemoContent { background: %s; }' % background)
        self.host.setStyleSheet('QWidget#drawerDemoHost { background: %s; }' % ('#303030' if dark else '#ffffff'))
