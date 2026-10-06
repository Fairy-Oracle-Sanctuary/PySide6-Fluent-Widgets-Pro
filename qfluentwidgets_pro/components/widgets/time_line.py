"""Grouped, theme-aware vertical timeline."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ...common.config import qconfig
from ...common.icon import drawIcon
from ...common.style_sheet import isDarkTheme
from ...common.style_sheet import themeColor
from .card_widget import CardWidget
from .info_bar import InfoBarIcon, InfoIconWidget
from .label import BodyLabel, StrongBodyLabel


class _TimeLineIconWidget(InfoIconWidget):
    """16px status glyph centered in the existing 36px layout cell."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        rect = QRectF(10, 10, 16, 16)
        if self.icon == InfoBarIcon.INFORMATION:
            drawIcon(self.icon, painter, rect, indexes=[0], fill=themeColor().name())
        else:
            drawIcon(self.icon, painter, rect)


class TimeLineItem(CardWidget):
    """Clickable timeline card; textLabel supports rich text and word wrapping.

    Connect ``clicked`` for the item's action. Its icon and text are display-only
    mouse targets, so the whole card shares CardWidget's hover/pressed animation.
    """

    def __init__(self, text, icon=InfoBarIcon.INFORMATION, parent=None):
        super().__init__(parent)
        self._mouseClickPending = False
        self.setClickEnabled(True)
        self.setBorderRadius(10)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.iconWidget = _TimeLineIconWidget(icon, self)
        self.textLabel = BodyLabel(text, self)
        self.iconWidget.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.textLabel.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.textLabel.setFocusPolicy(Qt.NoFocus)
        self.textLabel.setWordWrap(True)
        self.setMinimumHeight(50)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 7, 14, 7)
        layout.setSpacing(0)
        layout.addWidget(self.iconWidget, 0, Qt.AlignVCenter)
        layout.addWidget(self.textLabel, 1)

    def setText(self, text):
        self.textLabel.setText(text)

    def setIcon(self, icon):
        self.iconWidget.icon = icon
        self.iconWidget.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled() and self.isClickEnabled():
            self._mouseClickPending = True
            self.setFocus(Qt.MouseFocusReason)
            super().mousePressEvent(event)
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            event.ignore()
            return
        activate = (self._mouseClickPending and self.isEnabled() and self.isClickEnabled()
                    and self.rect().contains(event.position().toPoint()))
        self._mouseClickPending = False
        if activate:
            super().mouseReleaseEvent(event)
        else:
            # Avoid CardWidget's unconditional clicked signal for canceled presses.
            self.isPressed = False
            self._updateBackgroundColor()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            if not event.isAutoRepeat() and self.isEnabled() and self.isClickEnabled():
                self.clicked.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        self._mouseClickPending = False
        self.isPressed = False
        super().hideEvent(event)

    def changeEvent(self, event):
        if not self.isEnabled():
            self._mouseClickPending = False
            self.isPressed = False
        super().changeEvent(event)


class TimeLineGroup(QWidget):
    """Timeline section with a status header and an arbitrary number of cards."""

    def __init__(self, title, icon=InfoBarIcon.INFORMATION, parent=None):
        super().__init__(parent)
        self.items = []
        self.header = QWidget(self)
        self.header.setFixedHeight(36)
        self.iconWidget = _TimeLineIconWidget(icon, self.header)
        self.titleLabel = StrongBodyLabel(title, self.header)
        headerLayout = QHBoxLayout(self.header)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(4)
        headerLayout.addWidget(self.iconWidget)
        headerLayout.addWidget(self.titleLabel, 1)
        self.cards = QWidget(self)
        self.cardsLayout = QVBoxLayout(self.cards)
        self.cardsLayout.setContentsMargins(42, 0, 0, 12)
        self.cardsLayout.setSpacing(19)
        self.layoutBox = QVBoxLayout(self)
        self.layoutBox.setContentsMargins(0, 0, 0, 0)
        self.layoutBox.setSpacing(11)
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
    """Compact vertical timeline. addGroup() returns a section with addItem().

    The default maximum width is 370 logical pixels, giving 328px item cards.
    Use setMaximumWidth() / setFixedWidth() to customize the available width.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(370)
        self.groups = []
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(6)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        qconfig.themeChangedFinished.connect(self._updateTheme)
        qconfig.themeColorChanged.connect(self._updateTheme)

    def _updateTheme(self):
        self.update()
        for widget in self.findChildren(QWidget):
            widget.update()

    def sizeHint(self):
        size = super().sizeHint()
        size.setWidth(370)
        return size

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
