"""Non-activating page search results for FilledFluentWindow."""

from PySide6.QtCore import QEvent, QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect, QListWidgetItem, QVBoxLayout,
)

from ..common.font import setFont
from ..common.icon import toQIcon
from ..common.style_sheet import FluentStyleSheet, themeColor
from ..components.widgets.label import BodyLabel
from ..components.widgets.list_view import ListItemDelegate, ListWidget


class _PageSearchDelegate(ListItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Qt otherwise synthesizes a palette-tinted Selected icon.
        original = option.icon
        icon = QIcon(original)
        for state in (QIcon.Off, QIcon.On):
            pixmap = original.pixmap(option.decorationSize, QIcon.Normal, state)
            icon.addPixmap(pixmap, QIcon.Selected, state)
        option.icon = icon

    def _drawIndicator(self, painter, option, index):
        # Row spacing offsets option.rect; x=0 clips most of a 3px indicator.
        painter.setPen(Qt.NoPen)
        painter.setBrush(themeColor())
        height = min(16, option.rect.height())
        painter.drawRoundedRect(
            QRectF(option.rect.x() + 1, option.rect.center().y() - height / 2,
                   3, height), 1.5, 1.5
        )


class _PageSearchPopup(QFrame):
    activated = Signal(str)

    def __init__(self, lineEdit, parent):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.lineEdit = lineEdit
        self.owner = parent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.setObjectName('pageSearchPopup')
        self.card = QFrame(self)
        self.card.setObjectName('pageSearchCard')
        self.view = ListWidget(self.card)
        self.view.setItemDelegate(_PageSearchDelegate(self.view))
        self.view.setObjectName('pageSearchResults')
        self.view.setFocusPolicy(Qt.NoFocus)
        self.view.setIconSize(QSize(16, 16))
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setSpacing(2)
        setFont(self.view, 14)
        self.emptyLabel = BodyLabel(self.tr('No matching pages'), self.card)
        self.emptyLabel.setObjectName('pageSearchEmptyLabel')
        self.emptyLabel.setAlignment(Qt.AlignCenter)
        self.emptyLabel.setFixedHeight(44)
        self.cardLayout = QVBoxLayout(self.card)
        self.cardLayout.setContentsMargins(8, 8, 8, 8)
        self.cardLayout.addWidget(self.view)
        self.cardLayout.addWidget(self.emptyLabel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 14)
        layout.addWidget(self.card)
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 45))
        self.card.setGraphicsEffect(shadow)
        FluentStyleSheet.PAGE_SEARCH.apply(self)
        self.view.itemClicked.connect(self._activateItem)

    def setResults(self, results, preserveSelection=False):
        current = self.view.currentItem()
        route = current.data(Qt.UserRole) if current and preserveSelection else None
        self.view.clear()
        selected = 0
        for row, (key, text, icon) in enumerate(results):
            item = QListWidgetItem(toQIcon(icon), text)
            item.setData(Qt.UserRole, key)
            item.setToolTip(text)
            item.setSizeHint(QSize(1, 36))
            self.view.addItem(item)
            if key == route:
                selected = row
        self.view.setVisible(bool(results))
        self.emptyLabel.setVisible(not results)
        if results:
            self.view.setCurrentRow(selected)
        self.reposition()

    def reposition(self):
        screen = self.lineEdit.screen().availableGeometry()
        # The card aligns with the input; the extra 20 pixels are shadow margins.
        width = min(self.lineEdit.width() + 20, screen.width() - 16)
        self.view.ensurePolished()
        row_height = self.view.sizeHintForRow(0) if self.view.count() else 44
        height = min(8, max(1, self.view.count())) * (
            row_height + 2 * self.view.spacing()
        ) + 40
        below = self.lineEdit.mapToGlobal(QPoint(-10, self.lineEdit.height() - 3))
        above = self.lineEdit.mapToGlobal(QPoint(-10, 0))
        bottom = min(screen.bottom() - 8, self.owner.frameGeometry().bottom() - 8)
        available = bottom - below.y()
        y = below.y()
        if available < min(height, 100) and above.y() - screen.top() > available:
            height = min(height, above.y() - screen.top() - 8)
            y = above.y() - height
        else:
            height = min(height, max(60, available))
        x = max(screen.left() + 8, min(below.x(), screen.right() - width - 8))
        self.setFixedSize(max(120, width), max(60, height))
        self.move(x, y)

    def moveSelection(self, delta):
        if self.view.count():
            row = max(0, min(self.view.count() - 1, self.view.currentRow() + delta))
            self.view.setCurrentRow(row)
            self.view.scrollToItem(self.view.currentItem())

    def activateCurrent(self):
        item = self.view.currentItem()
        if item:
            self._activateItem(item)

    def _activateItem(self, item):
        key = item.data(Qt.UserRole)
        self.hide()
        self.activated.emit(key)

    def showEvent(self, event):
        super().showEvent(event)
        QApplication.instance().installEventFilter(self)

    def hideEvent(self, event):
        QApplication.instance().removeEventFilter(self)
        super().hideEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            pos = event.globalPosition().toPoint()
            edit_rect = self.lineEdit.rect().translated(self.lineEdit.mapToGlobal(QPoint()))
            if not self.frameGeometry().contains(pos) and not edit_rect.contains(pos):
                self.hide()
        elif obj is self.owner:
            if event.type() in (QEvent.Move, QEvent.Resize):
                self.reposition()
            elif event.type() in (QEvent.Hide, QEvent.WindowDeactivate):
                self.hide()
        return super().eventFilter(obj, event)
