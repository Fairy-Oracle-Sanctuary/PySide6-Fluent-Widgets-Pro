"""FilledFluentWindow showcase matching the expanded-sidebar reference."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QVBoxLayout, QWidget

from qfluentwidgets_pro import (
    ComboBox, FilledFluentWindow, FluentIcon, NavigationItemPosition,
    PushButton, SubtitleLabel, setThemeColor, toggleTheme,
)


class FilledWindowDemo(FilledFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FilledFluentWindow Demo')
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.resize(920, 700)
        self.setMinimumSize(600, 400)
        self.searchLineEdit.setPlaceholderText('搜索页面')
        self.searchLineEdit.setToolTip('搜索页面名称，例如：视频、音乐、设置')

        self.homeInterface, self.homeLabel = self._page('filledHome', 'Home Interface')
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, '主页')
        for key, icon, title, text in (
            ('filledMusic', FluentIcon.MUSIC, '音乐', 'Music Interface'),
            ('filledVideo', FluentIcon.VIDEO, '视频', 'Video Interface'),
            ('filledUpdate', FluentIcon.DOWNLOAD, '更新', 'Update Interface'),
        ):
            page, _ = self._page(key, text)
            position = NavigationItemPosition.BOTTOM if key == 'filledUpdate' else NavigationItemPosition.TOP
            self.addSubInterface(page, icon, title, position=position)

        self.settingsInterface, _ = self._page('filledSettings', 'Settings Interface')
        layout = self.settingsInterface.layout()
        theme_button = PushButton('切换浅色 / 深色', self.settingsInterface)
        theme_button.clicked.connect(toggleTheme)
        layout.addWidget(theme_button, 0, Qt.AlignHCenter)
        colors = ComboBox(self.settingsInterface)
        colors.addItems(['主题色：蓝色', '主题色：青绿色', '主题色：紫色'])
        colors.currentIndexChanged.connect(
            lambda index: setThemeColor(['#0078d4', '#009faa', '#8764b8'][index]))
        layout.addWidget(colors, 0, Qt.AlignHCenter)
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, '设置',
                             position=NavigationItemPosition.BOTTOM)

    def _page(self, name, text):
        page = QWidget(self)
        page.setObjectName(name)
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        label = SubtitleLabel(text, page)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return page, label
