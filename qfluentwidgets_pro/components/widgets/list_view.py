# coding:utf-8
from typing import List

from PySide6.QtCore import Property, QModelIndex, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import (
    QListView,
    QListWidget,
    QListWidgetItem,
    QStyleOptionViewItem,
    QWidget,
)

from ...common.color import autoFallbackThemeColor
from ...common.icon import FluentIconBase, Icon, drawIcon
from ...common.style_sheet import FluentStyleSheet, isDarkTheme, themeColor
from .scroll_bar import SmoothScrollDelegate
from .table_view import TableItemDelegate


class ListItemDelegate(TableItemDelegate):
    """List item delegate"""

    def __init__(self, parent: QListView):
        super().__init__(parent)

    def _drawBackground(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        painter.drawRoundedRect(option.rect, 5, 5)

    def _drawIndicator(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        y, h = option.rect.y(), option.rect.height()
        ph = round(0.35 * h if self.pressedRow == index.row() else 0.257 * h)
        painter.setBrush(
            autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor)
        )
        painter.drawRoundedRect(0, ph + y, 3, h - 2 * ph, 1.5, 1.5)


class ListBase:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delegate = ListItemDelegate(self)
        self.scrollDelegate = SmoothScrollDelegate(self)
        self._isSelectRightClickedRow = False

        FluentStyleSheet.LIST_VIEW.apply(self)
        self.setItemDelegate(self.delegate)
        self.setMouseTracking(True)

        self.entered.connect(lambda i: self._setHoverRow(i.row()))
        self.pressed.connect(lambda i: self._setPressedRow(i.row()))

    def _setHoverRow(self, row: int):
        """set hovered row"""
        self.delegate.setHoverRow(row)
        self.viewport().update()

    def _setPressedRow(self, row: int):
        """set pressed row"""
        if self.selectionMode() == QListView.SelectionMode.NoSelection:
            return

        self.delegate.setPressedRow(row)
        self.viewport().update()

    def _setSelectedRows(self, indexes: List[QModelIndex]):
        if self.selectionMode() == QListView.SelectionMode.NoSelection:
            return

        self.delegate.setSelectedRows(indexes)
        self.viewport().update()

    def leaveEvent(self, e):
        QListView.leaveEvent(self, e)
        self._setHoverRow(-1)

    def resizeEvent(self, e):
        QListView.resizeEvent(self, e)
        self.viewport().update()

    def keyPressEvent(self, e):
        QListView.keyPressEvent(self, e)
        self.updateSelectedRows()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton or self._isSelectRightClickedRow:
            return QListView.mousePressEvent(self, e)

        index = self.indexAt(e.pos())
        if index.isValid():
            self._setPressedRow(index.row())

        QWidget.mousePressEvent(self, e)

    def mouseReleaseEvent(self, e):
        QListView.mouseReleaseEvent(self, e)
        self.updateSelectedRows()

        if self.indexAt(e.pos()).row() < 0 or e.button() == Qt.RightButton:
            self._setPressedRow(-1)

    def setItemDelegate(self, delegate: ListItemDelegate):
        self.delegate = delegate
        super().setItemDelegate(delegate)

    def clearSelection(self):
        QListView.clearSelection(self)
        self.updateSelectedRows()

    def setCurrentIndex(self, index: QModelIndex):
        QListView.setCurrentIndex(self, index)
        self.updateSelectedRows()

    def updateSelectedRows(self):
        self._setSelectedRows(self.selectedIndexes())

    def setCheckedColor(self, light, dark):
        """set the color in checked status

        Parameters
        ----------
        light, dark: str | QColor | Qt.GlobalColor
            color in light/dark theme mode
        """
        self.delegate.setCheckedColor(light, dark)


class ListWidget(ListBase, QListWidget):
    """List widget"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def setCurrentItem(self, item, command=None):
        self.setCurrentRow(self.row(item), command)

    def setCurrentRow(self, row: int, command=None):
        if not command:
            super().setCurrentRow(row)
        else:
            super().setCurrentRow(row, command)

        self.updateSelectedRows()

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(
        bool, isSelectRightClickedRow, setSelectRightClickedRow
    )


class ListView(ListBase, QListView):
    """List view"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(
        bool, isSelectRightClickedRow, setSelectRightClickedRow
    )


class RoundListItemDelegate(ListItemDelegate):
    """Round list item delegate with no indicator and theme-aware icon support"""

    def __init__(self, parent: QListView):
        super().__init__(parent)
        self.showIndicator = False
        self._transparentSelection = False
        self._keepNormalBackground = False

    def setTransparentSelection(self, transparent: bool):
        """Set whether selected items should have transparent background"""
        self._transparentSelection = transparent

    def isTransparentSelection(self):
        return self._transparentSelection

    transparentSelection = Property(
        bool, isTransparentSelection, setTransparentSelection
    )

    def setKeepNormalBackground(self, keep: bool):
        """Set whether selected items should keep normal background color"""
        self._keepNormalBackground = keep

    def isKeepNormalBackground(self):
        return self._keepNormalBackground

    keepNormalBackground = Property(
        bool, isKeepNormalBackground, setKeepNormalBackground
    )

    def _drawIndicator(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Do not draw indicator"""
        pass

    def _drawIcon(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Draw theme-aware icon"""
        icon = index.data(Qt.DecorationRole)
        if icon is None:
            return

        # Icon position: left side with padding
        iconSize = 16
        x = option.rect.x() + 16
        y = option.rect.y() + (option.rect.height() - iconSize) // 2
        rect = QRectF(x, y, iconSize, iconSize)

        if isinstance(icon, (FluentIconBase, Icon)):
            if isinstance(icon, FluentIconBase):
                if index.row() in self.selectedRows:
                    icon = icon.icon(color=themeColor())
                else:
                    icon = icon.icon()
            drawIcon(icon, painter, rect)
        elif isinstance(icon, QIcon):
            # Regular QIcon
            icon.paint(painter, rect.toRect(), Qt.AlignCenter)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # Draw background based on state
        isHover = self.hoverRow == index.row()
        isSelected = index.row() in self.selectedRows
        isDark = isDarkTheme()

        # Determine if we should draw background
        shouldDrawBg = True
        if self._transparentSelection and isSelected and not isHover:
            shouldDrawBg = False

        if shouldDrawBg:
            # Get background color from QSS via option.backgroundBrush
            if option.backgroundBrush and option.backgroundBrush.style() != Qt.NoBrush:
                painter.setBrush(option.backgroundBrush)
            else:
                # Fallback: draw background manually
                c = 255 if isDark else 0
                if isSelected and not self._keepNormalBackground:
                    alpha = 17
                elif isHover:
                    alpha = 12
                else:
                    alpha = 0
                painter.setBrush(QColor(c, c, c, alpha))

            # Draw rounded background
            rect = option.rect.adjusted(1, 1, -1, -1)
            painter.drawRoundedRect(rect, 5, 5)

        painter.restore()

        # Call parent paint to draw text
        from PySide6.QtWidgets import QStyledItemDelegate

        QStyledItemDelegate.paint(self, painter, option, index)

        # Draw icon on top
        painter.save()
        self._drawIcon(painter, option, index)
        painter.restore()


class RoundListBase(ListBase):
    """Round list base with border and background styling"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delegate = RoundListItemDelegate(self)
        self.setItemDelegate(self.delegate)
        self.setSpacing(1)


class RoundListWidget(RoundListBase, QListWidget):
    """Round list widget with border, background, no indicator, and icon support"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def addItem(self, text: str, icon=None):
        """Add an item with optional icon

        Parameters
        ----------
        text : str
            Item text
        icon : FluentIconBase | QIcon | None
            Optional icon (FluentIcon for theme support, or QIcon)
        """
        item = QListWidgetItem(self)
        item.setText(text)
        if icon is not None:
            item.setData(Qt.DecorationRole, icon)
        super().addItem(item)

    def addItems(self, items: list):
        """Add multiple items

        Parameters
        ----------
        items : list
            List of items, each can be:
            - str: item text without icon
            - tuple (text, icon): item text with icon
        """
        for item in items:
            if isinstance(item, tuple):
                self.addItem(item[0], item[1] if len(item) > 1 else None)
            else:
                self.addItem(item)

    def setCurrentItem(self, item, command=None):
        self.setCurrentRow(self.row(item), command)

    def setCurrentRow(self, row: int, command=None):
        if not command:
            super().setCurrentRow(row)
        else:
            super().setCurrentRow(row, command)
        self.updateSelectedRows()

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(
        bool, isSelectRightClickedRow, setSelectRightClickedRow
    )


class RoundListView(RoundListBase, QListView):
    """Round list view with border, background, no indicator, and icon support"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(
        bool, isSelectRightClickedRow, setSelectRightClickedRow
    )


class TransparentRoundListWidget(RoundListWidget):
    """Transparent Round List Widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.delegate.setTransparentSelection(True)


class TransparentRoundListView(RoundListView):
    """Transparent Round List View"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.delegate.setTransparentSelection(True)


class CategoryCardListWidget(RoundListWidget):
    """CategoryCard List Widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.delegate.setKeepNormalBackground(True)


class CategoryCardListView(RoundListView):
    """CategoryCard List View"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.delegate.setKeepNormalBackground(True)
