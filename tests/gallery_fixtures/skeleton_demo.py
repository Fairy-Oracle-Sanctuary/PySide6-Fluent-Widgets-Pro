"""Native animated loading skeleton examples."""

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import (
    ArticleSkeleton, BodyLabel, CardWidget, CheckBox, CirclePersonalInfoSkeleton,
    PushButton, RectanglePersonalInfoSkeleton, ScrollArea, SkeletonWidget, toggleTheme,
)
from qfluentwidgets_pro.common.config import qconfig
from qfluentwidgets_pro.common.style_sheet import isDarkTheme


class _CustomSkeleton(SkeletonWidget):
    """Example of a responsive custom path with a fixed avatar/text gap."""

    def skeletonPath(self):
        path = super().skeletonPath()
        avatar = min(100., self.height(), self.width() / 4)
        left = avatar + min(20., max(0., self.width() - avatar))
        width = max(0., min(400., self.width() - left))
        path.addEllipse(QRectF(0, (self.height() - avatar) / 2, avatar, avatar))
        y = (self.height() - 100) / 2
        for top in (10, 60):
            path.addRoundedRect(QRectF(left, y + top, width, 30), 6, 6)
        return path


class SkeletonDemo(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('skeletonInterface')
        self.setWidgetResizable(True)
        page = QWidget()
        page.setObjectName('skeletonDemoContent')
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(18)
        header = QHBoxLayout()
        header.addWidget(BodyLabel('Skeleton — 扫光骨架组件', page))
        header.addStretch()
        self.animationCheckBox = CheckBox('扫光动画', page)
        self.animationCheckBox.setChecked(True)
        header.addWidget(self.animationCheckBox)
        theme = PushButton('切换主题', page)
        theme.clicked.connect(toggleTheme)
        header.addWidget(theme)
        layout.addLayout(header)
        layout.addWidget(BodyLabel('加载占位，不读取真实内容。关闭扫光可显示静态骨架。', page))
        self.skeletons = [ArticleSkeleton(), CirclePersonalInfoSkeleton(),
                          RectanglePersonalInfoSkeleton(), _CustomSkeleton()]
        for title, skeleton in zip(('文章信息骨架', '圆形个人信息骨架', '方形个人信息骨架', '自定义骨架'), self.skeletons):
            layout.addWidget(BodyLabel(title, page))
            card = CardWidget(page)
            card.setBorderRadius(8)
            content = QVBoxLayout(card)
            content.setContentsMargins(16, 14, 16, 14)
            content.addWidget(skeleton)
            layout.addWidget(card)
        layout.addStretch()
        self.setWidget(page)
        self.animationCheckBox.toggled.connect(self._toggleAnimation)
        qconfig.themeChangedFinished.connect(self._applyTheme)
        self._applyTheme()

    def _applyTheme(self):
        background = '#262626' if isDarkTheme() else '#f3f3f3'
        self.setStyleSheet('QScrollArea#skeletonInterface { background: %s; border: none; }' % background)
        self.widget().setStyleSheet('QWidget#skeletonDemoContent { background: %s; }' % background)

    def _toggleAnimation(self, enabled):
        for skeleton in self.skeletons:
            skeleton.setAnimationEnabled(enabled)
