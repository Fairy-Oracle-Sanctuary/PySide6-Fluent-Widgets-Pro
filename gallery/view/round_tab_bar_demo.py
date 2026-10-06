"""RoundTabBar switching, application-managed pages and interactive settings."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from qfluentwidgets_pro import (
    BodyLabel, CheckBox, ComboBox, RoundTabBar, SpinBox,
    TabCloseButtonDisplayMode, isDarkTheme, qconfig,
)


class _TabSurface(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        qconfig.themeChangedFinished.connect(self.update)

    def paintEvent(self, event):
        light = self.property('lightBackgroundColor') or '#f9f9f9'
        QPainter(self).fillRect(self.rect(), QColor('#1b2030' if isDarkTheme() else light))


class _TabControls(_TabSurface):
    def paintEvent(self, event):
        QPainter(self).fillRect(self.rect(), QColor('#282828' if isDarkTheme() else '#f3f3f3'))


class RoundTabBarDemo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pages = {}
        self._number = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(12)
        layout.addWidget(BodyLabel('RoundTabBar — 圆角标签栏', self))
        preview = QHBoxLayout()
        preview.setSpacing(0)
        self.surface = _TabSurface(self)
        self.surface.setMinimumHeight(250)
        surfaceLayout = QVBoxLayout(self.surface)
        surfaceLayout.setContentsMargins(0, 0, 0, 0)
        surfaceLayout.setSpacing(0)
        self.tabBar = RoundTabBar(self.surface)
        self.tabBar.setTabSelectedBackgroundColor(QColor('#f9f9f9'), QColor('#252a38'))
        self.stack = QStackedWidget(self.surface)
        surfaceLayout.addWidget(self.tabBar)
        surfaceLayout.addWidget(self.stack, 1)
        preview.addWidget(self.surface, 1)
        controls = _TabControls(self)
        controls.setFixedWidth(220)
        options = QVBoxLayout(controls)
        options.setContentsMargins(16, 16, 16, 16)
        options.setSpacing(12)
        self.movableCheckBox = CheckBox('是否可拖拽', controls)
        self.scrollableCheckBox = CheckBox('是否可滚动', controls)
        options.addWidget(self.movableCheckBox)
        options.addWidget(self.scrollableCheckBox)
        options.addWidget(BodyLabel('标签最大宽度', controls))
        self.maximumWidthBox = SpinBox(controls)
        self.maximumWidthBox.setRange(64, 400)
        self.maximumWidthBox.setValue(200)
        options.addWidget(self.maximumWidthBox)
        options.addWidget(BodyLabel('关闭按钮显示模式', controls))
        self.closeModeBox = ComboBox(controls)
        self.closeModeBox.addItems(['始终显示', '悬停显示', '不显示'])
        options.addWidget(self.closeModeBox)
        options.addStretch()
        preview.addWidget(controls)
        layout.addLayout(preview)
        self.movableCheckBox.toggled.connect(self.tabBar.setMovable)
        self.scrollableCheckBox.toggled.connect(self.tabBar.setScrollable)
        self.maximumWidthBox.valueChanged.connect(self.tabBar.setTabMaximumWidth)
        self.closeModeBox.currentIndexChanged.connect(
            lambda index: self.tabBar.setCloseButtonDisplayMode(list(TabCloseButtonDisplayMode)[index]))
        self.tabBar.currentChanged.connect(self._syncPage)
        self.tabBar.tabMoved.connect(self._syncPage)
        self.tabBar.tabAddRequested.connect(self._addRequested)
        self.tabBar.tabCloseRequested.connect(self._closeRequested)
        self._addPage('songs', '\U0001f3b5 歌曲', 'Song Interface')
        self._addPage('albums', '\U0001f4c0 专辑', 'Album Interface')
        self._addPage('artists', '\U0001f469\u200d\U0001f3a4 歌手', 'Artist Interface')
        self.tabBar.setCurrentTab('albums')
        self._syncPage()

    def _addPage(self, key, title, content):
        page = QWidget(self.stack)
        pageLayout = QVBoxLayout(page)
        pageLayout.setContentsMargins(26, 12, 26, 12)
        pageLayout.addWidget(BodyLabel(content, page))
        pageLayout.addStretch()
        self.pages[key] = page
        self.stack.addWidget(page)
        self.tabBar.addTab(key, title)

    def _addRequested(self):
        self._number += 1
        key = f'new-{self._number}'
        self._addPage(key, f'新标签 {self._number}', f'New Interface {self._number}')
        self.tabBar.setCurrentTab(key)
        self._syncPage()

    def _closeRequested(self, index):
        item = self.tabBar.tabItem(index)
        if item is None:
            return
        key = item.routeKey()
        self.tabBar.removeTab(index)
        page = self.pages.pop(key)
        self.stack.removeWidget(page)
        page.deleteLater()
        self._syncPage()

    def _syncPage(self, *args):
        item = self.tabBar.currentTab()
        if item is not None and item.routeKey() in self.pages:
            self.stack.setCurrentWidget(self.pages[item.routeKey()])
