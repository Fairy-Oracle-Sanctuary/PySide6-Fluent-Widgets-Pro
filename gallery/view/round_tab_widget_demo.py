"""QTabWidget-style user pages in a RoundTabWidget."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QVBoxLayout, QWidget

from qfluentwidgets_pro import BodyLabel, RoundTabWidget, setFont


class RoundTabWidgetDemo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._number = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(12)
        layout.addWidget(BodyLabel('RoundTabWidget — 圆角标签页', self))
        self.tabWidget = RoundTabWidget(self)
        self.tabWidget.setMinimumHeight(320)
        self.tabWidget.setMovable(True)
        self.tabWidget.setTabMaximumWidth(240)
        self.tabWidget.tabAddRequested.connect(self._addPage)
        self.tabWidget.tabCloseRequested.connect(self._closePage)
        layout.addWidget(self.tabWidget)
        self._addPage()
        self._addPage()
        self.tabWidget.setCurrentIndex(0)

    def _addPage(self):
        self._number += 1
        text = f'硝子酱一级棒卡哇伊×{self._number}'
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(12)
        layout.addStretch()
        emoji = BodyLabel('\U0001f970', page)
        font = QFont('Segoe UI Emoji')
        font.setPixelSize(80)
        emoji.setFont(font)
        emoji.setAlignment(Qt.AlignCenter)
        layout.addWidget(emoji)
        title = BodyLabel(text, page)
        setFont(title, 20)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addStretch()
        index = self.tabWidget.addTab(page, f'\U0001f970 {text}')
        self.tabWidget.setCurrentIndex(index)

    def _closePage(self, index):
        page = self.tabWidget.widget(index)
        self.tabWidget.removeTab(index)
        if page is not None:
            page.deleteLater()
