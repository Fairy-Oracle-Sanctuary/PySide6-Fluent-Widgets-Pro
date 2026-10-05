"""Grouped, theme-aware vertical timeline."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ...common.config import qconfig
from ...common.style_sheet import isDarkTheme
from .info_bar import InfoBarIcon, InfoIconWidget
from .label import BodyLabel


class TimeLineItem(QWidget):
    """A timeline card; textLabel supports rich text and word wrapping."""

    def __init__(self, text, icon=InfoBarIcon.INFORMATION, parent=None):
        super().__init__(parent)
        self.iconWidget = InfoIconWidget(icon, self)
        self.textLabel = BodyLabel(text, self)
        self.textLabel.setWordWrap(True)
        self.setMinimumHeight(62)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 12, 18, 12)
        layout.setSpacing(4)
        layout.addWidget(self.iconWidget, 0, Qt.AlignVCenter)
        layout.addWidget(self.textLabel, 1)

    def setText(self, text):
        self.textLabel.setText(text)

    def setIcon(self, icon):
        self.iconWidget.icon = icon
        self.iconWidget.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        dark = isDarkTheme()
        painter.setBrush(QColor(255, 255, 255, 8 if dark else 180))
        painter.setPen(QPen(QColor(255, 255, 255, 15) if dark
                            else QColor(0, 0, 0, 15), 1))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 10, 10)


class TimeLineGroup(QWidget):
    """Timeline section with a status header and an arbitrary number of cards."""

    def __init__(self, title, icon=InfoBarIcon.INFORMATION, parent=None):
        super().__init__(parent)
        self.items = []
        self.header = QWidget(self)
        self.header.setFixedHeight(36)
        self.iconWidget = InfoIconWidget(icon, self.header)
        self.titleLabel = BodyLabel(title, self.header)
        headerLayout = QHBoxLayout(self.header)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(10)
        headerLayout.addWidget(self.iconWidget)
        headerLayout.addWidget(self.titleLabel, 1)
        self.cards = QWidget(self)
        self.cardsLayout = QVBoxLayout(self.cards)
        self.cardsLayout.setContentsMargins(48, 0, 0, 16)
        self.cardsLayout.setSpacing(24)
        self.layoutBox = QVBoxLayout(self)
        self.layoutBox.setContentsMargins(0, 0, 0, 0)
        self.layoutBox.setSpacing(18)
        self.layoutBox.addWidget(self.header)
        self.layoutBox.addWidget(self.cards)
        self.cards.hide()

    def addItem(self, text, icon=InfoBarIcon.INFORMATION):
        item = TimeLineItem(text, icon, self.cards)
        self.items.append(item)
        self.cardsLayout.addWidget(item)
        self.cards.show()
        return item

    def removeItem(self, item):
        if item not in self.items:
            return
        self.items.remove(item)
        self.cardsLayout.removeWidget(item)
        item.hide()
        item.deleteLater()
        self.cards.setVisible(bool(self.items))
        self.update()

    def paintEvent(self, event):
        if not self.items:
            return
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 255, 90) if isDarkTheme()
                            else QColor(0, 0, 0, 100), 1))
        painter.drawLine(18, self.header.height() + 6, 18, self.height() - 1)


class TimeLineWidget(QWidget):
    """Vertical timeline. addGroup() returns a section with addItem()."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.groups = []
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        qconfig.themeChangedFinished.connect(self._updateTheme)
        qconfig.themeColorChanged.connect(self._updateTheme)

    def _updateTheme(self):
        self.update()
        for widget in self.findChildren(QWidget):
            widget.update()

    def addGroup(self, title, icon=InfoBarIcon.INFORMATION):
        group = TimeLineGroup(title, icon, self)
        self.groups.append(group)
        self.vBoxLayout.addWidget(group)
        return group

    def removeGroup(self, group):
        if group not in self.groups:
            return
        self.groups.remove(group)
        self.vBoxLayout.removeWidget(group)
        group.hide()
        group.deleteLater()

    def clear(self):
        for group in self.groups[:]:
            self.removeGroup(group)
