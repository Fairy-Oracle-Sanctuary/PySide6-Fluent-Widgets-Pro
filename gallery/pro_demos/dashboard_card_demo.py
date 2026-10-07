"""Dashboard cards with text, custom content and theme-aware backgrounds."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import (
    BodyLabel, DashboardCardWidget, FluentIcon, PushButton, ScrollArea, getFont, toggleTheme,
)
from qfluentwidgets_pro.common.config import qconfig
from qfluentwidgets_pro.common.style_sheet import isDarkTheme


def emojiIcon(text):
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    font = getFont(48)
    font.setFamily('Segoe UI Emoji')
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
    painter.end()
    return QIcon(pixmap)


class DashboardCardDemo(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('dashboardCardInterface')
        self.setWidgetResizable(True)
        page = QWidget()
        page.setObjectName('dashboardCardDemoContent')
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(16)
        header = QHBoxLayout()
        header.addWidget(BodyLabel('DashboardCardWidget — 仪表盘卡片', page))
        header.addStretch()
        theme = PushButton('切换主题', page)
        theme.clicked.connect(toggleTheme)
        header.addWidget(theme)
        layout.addLayout(header)
        layout.addWidget(BodyLabel('仪表盘卡片：图标、标题、开关和说明文字', page))
        self.featureCard = DashboardCardWidget(
            emojiIcon('🔓'), 'File Locksmith', '右击文件或文件夹以显示正在运行的进程', page)
        self.featureCard.setCardBackgroundColor('#fff7e8', '#34312a')
        self.featureCard.setChecked(True)
        self.featureCard.setFixedWidth(400)
        layout.addWidget(self.featureCard, 0, Qt.AlignLeft)
        layout.addSpacing(16)
        layout.addWidget(BodyLabel('自定义仪表盘卡片：内容区域可以加入任意 QWidget / 布局', page))
        self.customCard = DashboardCardWidget(emojiIcon('🌐'), 'Hosts 文件编辑器', parent=page)
        self.customCard.setCardBackgroundColor('#edf7fa', '#282e30')
        self.customCard.setFixedWidth(400)
        self.openButton = PushButton('打开文件编辑器', self.customCard)
        self.customCard.addWidget(self.openButton)
        layout.addWidget(self.customCard, 0, Qt.AlignLeft)
        layout.addSpacing(16)
        layout.addWidget(BodyLabel('默认背景：保留 SimpleCardWidget 原有的主题背景和描边', page))
        self.defaultCard = DashboardCardWidget(
            FluentIcon.SETTING, '自定义功能', '只绘制卡片和报告开关状态，不内置实际业务逻辑。', page)
        self.defaultCard.setFixedWidth(400)
        layout.addWidget(self.defaultCard, 0, Qt.AlignLeft)
        self.status = BodyLabel('点击开关或自定义按钮，观察状态变化。', page)
        layout.addWidget(self.status)
        layout.addStretch()
        self.featureCard.checkedChanged.connect(lambda value: self.status.setText(f'File Locksmith：{"开启" if value else "关闭"}'))
        self.customCard.checkedChanged.connect(lambda value: self.status.setText(f'Hosts 文件编辑器：{"开启" if value else "关闭"}'))
        self.openButton.clicked.connect(lambda: self.status.setText('自定义按钮已点击；应用可在此连接实际编辑器。'))
        self.setWidget(page)
        qconfig.themeChangedFinished.connect(self._applyTheme)
        self._applyTheme()

    def _applyTheme(self):
        background = '#262626' if isDarkTheme() else '#f3f3f3'
        self.setStyleSheet('QScrollArea#dashboardCardInterface { background: %s; border: none; }' % background)
        self.widget().setStyleSheet('QWidget#dashboardCardDemoContent { background: %s; }' % background)
