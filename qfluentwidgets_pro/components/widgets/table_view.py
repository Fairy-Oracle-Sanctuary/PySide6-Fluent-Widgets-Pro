# coding: utf-8
from typing import List

from PySide6.QtCore import Property, QMargins, QModelIndex, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QHelpEvent, QKeyEvent, QPainter, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ...common.color import autoFallbackThemeColor
from ...common.font import getFont
from ...common.style_sheet import (
    FluentStyleSheet,
    isDarkTheme,
    setCustomStyleSheet,
    themeColor,
    updateDynamicStyle,
)
from .check_box import CheckBoxIcon
from .line_edit import LineEdit
from .scroll_bar import SmoothScrollDelegate
from .tool_tip import ItemViewToolTipDelegate, ItemViewToolTipType


class TableItemDelegate(QStyledItemDelegate):
    def __init__(self, parent: QTableView):
        super().__init__(parent)
        self.margin = 2
        self.hoverRow = -1
        self.pressedRow = -1
        self.selectedRows = set()
        self.lightCheckedColor = QColor()
        self.darkCheckedColor = QColor()
        self.showIndicator = True
        self.borderRadius = 5
        self.useStackedWidgetStyle = False
        self.useTransparentRows = False
        self.useThemeColorSelection = False
        self.showRowDivider = False

        if isinstance(parent, QTableView):
            self.tooltipDelegate = ItemViewToolTipDelegate(
                parent, 100, ItemViewToolTipType.TABLE
            )
        else:
            self.tooltipDelegate = ItemViewToolTipDelegate(
                parent, 100, ItemViewToolTipType.LIST
            )

    def setHoverRow(self, row: int):
        self.hoverRow = row

    def setPressedRow(self, row: int):
        self.pressedRow = row

    def setSelectedRows(self, indexes: List[QModelIndex]):
        self.selectedRows.clear()
        for index in indexes:
            self.selectedRows.add(index.row())
            if index.row() == self.pressedRow:
                self.pressedRow = -1

    def setShowIndicator(self, show: bool):
        """Set whether to show selection indicator"""
        self.showIndicator = show

    def setBorderRadius(self, radius: int):
        """Set border radius for row background"""
        self.borderRadius = radius

    def setUseStackedWidgetStyle(self, use: bool):
        """Set whether to use StackedWidget style for alternating rows"""
        self.useStackedWidgetStyle = use

    def setUseTransparentRows(self, use: bool):
        """Set whether all rows are transparent (no alternating style)"""
        self.useTransparentRows = use

    def setUseThemeColorSelection(self, use: bool):
        """Set whether selected rows use theme color background"""
        self.useThemeColorSelection = use

    def setShowRowDivider(self, show: bool):
        """Set whether to show 1px divider line between rows"""
        self.showRowDivider = show

    def sizeHint(self, option, index):
        # increase original sizeHint to accommodate space needed for border
        size = super().sizeHint(option, index)
        size = size.grownBy(QMargins(0, self.margin, 0, self.margin))
        return size

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        lineEdit = LineEdit(parent)
        lineEdit.setProperty("transparent", False)
        lineEdit.setStyle(QApplication.style())
        lineEdit.setText(option.text)
        lineEdit.setClearButtonEnabled(True)
        return lineEdit

    def updateEditorGeometry(
        self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        rect = option.rect
        y = rect.y() + (rect.height() - editor.height()) // 2
        x, w = max(8, rect.x()), rect.width()
        if index.column() == 0:
            w -= 8

        editor.setGeometry(x, y, w, rect.height())

    def setCheckedColor(self, light, dark):
        """set the color of indicator in checked status

        Parameters
        ----------
        light, dark: str | QColor | Qt.GlobalColor
            color in light/dark theme mode
        """
        self.lightCheckedColor = QColor(light)
        self.darkCheckedColor = QColor(dark)
        self.parent().viewport().update()

    def _drawBackground(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """draw row background"""
        r = self.borderRadius
        if r == 0:
            # No border radius - draw full width without padding
            rect = option.rect.adjusted(-1, 0, 1, 0)
            painter.drawRect(rect)
        elif index.column() == 0:
            rect = option.rect.adjusted(4, 0, r + 1, 0)
            painter.drawRoundedRect(rect, r, r)
        elif index.column() == index.model().columnCount(index.parent()) - 1:
            rect = option.rect.adjusted(-r - 1, 0, -4, 0)
            painter.drawRoundedRect(rect, r, r)
        else:
            rect = option.rect.adjusted(-1, 0, 1, 0)
            painter.drawRect(rect)

    def _drawIndicator(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """draw indicator"""
        y, h = option.rect.y(), option.rect.height()
        ph = round(0.35 * h if self.pressedRow == index.row() else 0.257 * h)
        painter.setBrush(
            autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor)
        )
        painter.drawRoundedRect(4, ph + y, 3, h - 2 * ph, 1.5, 1.5)

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
        super().initStyleOption(option, index)

        # font
        option.font = index.data(Qt.FontRole) or getFont(13)

        # text color
        textColor = Qt.white if isDarkTheme() else Qt.black
        textBrush = index.data(Qt.ForegroundRole)  # type: QBrush
        if textBrush is not None:
            textColor = QBrush(textBrush).color()

        option.palette.setColor(QPalette.Text, textColor)
        option.palette.setColor(QPalette.HighlightedText, textColor)

    def paint(self, painter, option, index):
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing)

        # set clipping rect of painter to avoid painting outside the borders
        painter.setClipping(True)
        painter.setClipRect(option.rect)

        # call original paint method where option.rect is adjusted to account for border
        option.rect.adjust(0, self.margin, 0, -self.margin)

        # draw highlight background
        isHover = self.hoverRow == index.row()
        isPressed = self.pressedRow == index.row()
        isAlternate = index.row() % 2 == 0 and self.parent().alternatingRowColors()
        isSelected = index.row() in self.selectedRows
        isDark = isDarkTheme()

        c = 255 if isDark else 0
        alpha = 0

        if not isSelected:
            if isPressed:
                alpha = 9 if isDark else 6
            elif isHover:
                alpha = 12
            elif isAlternate:
                alpha = 5
        else:
            if isPressed:
                alpha = 15 if isDark else 9
            elif isHover:
                alpha = 25
            else:
                alpha = 17

        if index.data(Qt.ItemDataRole.BackgroundRole):
            painter.setBrush(index.data(Qt.ItemDataRole.BackgroundRole))
        elif self.useThemeColorSelection and isSelected:
            # Selected rows use theme color background

            color = themeColor()
            if isHover:
                bgColor = QColor(color.red(), color.green(), color.blue(), 40)
            elif isPressed:
                bgColor = QColor(color.red(), color.green(), color.blue(), 60)
            else:
                bgColor = QColor(color.red(), color.green(), color.blue(), 30)
            painter.setBrush(bgColor)
        elif self.useTransparentRows:
            # All rows transparent, selected rows show StackedWidget style
            if isSelected and not isHover and not isPressed:
                if isDark:
                    bgColor = QColor(255, 255, 255, 8)
                else:
                    bgColor = QColor(255, 255, 255, 127)
                painter.setBrush(bgColor)
            else:
                painter.setBrush(QColor(c, c, c, alpha))
        elif self.useStackedWidgetStyle:
            shouldUseStyle = isAlternate or (isSelected and not isAlternate)
            if shouldUseStyle and not isHover and not isPressed:
                if isDark:
                    bgColor = QColor(255, 255, 255, 8)
                else:
                    bgColor = QColor(255, 255, 255, 127)
                painter.setBrush(bgColor)
            else:
                painter.setBrush(QColor(c, c, c, alpha))
        else:
            painter.setBrush(QColor(c, c, c, alpha))

        self._drawBackground(painter, option, index)

        # Draw 1px border for StackedWidget style rows (only when not hover/pressed)
        if (
            (self.useStackedWidgetStyle or self.useTransparentRows)
            and not isHover
            and not isPressed
            and not index.data(Qt.ItemDataRole.BackgroundRole)
        ):
            if self.useTransparentRows:
                shouldDrawBorder = isSelected
            else:
                shouldDrawBorder = isAlternate or (isSelected and not isAlternate)
            if shouldDrawBorder:
                if isDark:
                    borderColor = QColor(0, 0, 0, 46)
                else:
                    borderColor = QColor(0, 0, 0, 17)
                painter.setPen(borderColor)
                painter.setBrush(Qt.NoBrush)
                self._drawBackground(painter, option, index)
                painter.setPen(Qt.NoPen)

        # draw indicator
        if (
            self.showIndicator
            and isSelected
            and index.column() == 0
            and self.parent().horizontalScrollBar().value() == 0
        ):
            self._drawIndicator(painter, option, index)

        if index.data(Qt.CheckStateRole) is not None:
            self._drawCheckBox(painter, option, index)

        # draw row divider line
        if self.showRowDivider and index.column() == 0:
            # Temporarily disable clipping to draw across full width
            painter.setClipping(False)
            y = option.rect.y() + option.rect.height() + self.margin
            painter.setPen(Qt.NoPen)
            if isDark:
                painter.setBrush(QColor(255, 255, 255, 47))
            else:
                painter.setBrush(QColor(0, 0, 0, 17))
            header = self.parent().horizontalHeader()
            totalWidth = header.length()
            rect = QRectF(0, y - 1, totalWidth, 1)
            painter.drawRect(rect)
            painter.setClipping(True)

        painter.restore()
        super().paint(painter, option, index)

    def _drawCheckBox(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        painter.save()
        checkState = Qt.CheckState(index.data(Qt.ItemDataRole.CheckStateRole))

        isDark = isDarkTheme()

        r = 4.5
        x = option.rect.x() + 15
        y = option.rect.center().y() - 9.5
        rect = QRectF(x, y, 19, 19)

        if checkState == Qt.CheckState.Unchecked:
            painter.setBrush(QColor(0, 0, 0, 26) if isDark else QColor(0, 0, 0, 6))
            painter.setPen(
                QColor(255, 255, 255, 142) if isDark else QColor(0, 0, 0, 122)
            )
            painter.drawRoundedRect(rect, r, r)
        else:
            color = autoFallbackThemeColor(
                self.lightCheckedColor, self.darkCheckedColor
            )
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRoundedRect(rect, r, r)

            if checkState == Qt.CheckState.Checked:
                CheckBoxIcon.ACCEPT.render(painter, rect)
            else:
                CheckBoxIcon.PARTIAL_ACCEPT.render(painter, rect)

        painter.restore()

    def helpEvent(
        self,
        event: QHelpEvent,
        view: QAbstractItemView,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        return self.tooltipDelegate.helpEvent(event, view, option, index)


class TableBase:
    """Table base class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delegate = TableItemDelegate(self)
        self.scrollDelagate = SmoothScrollDelegate(self)
        self._isSelectRightClickedRow = False

        # set style sheet
        FluentStyleSheet.TABLE_VIEW.apply(self)

        self.setShowGrid(False)
        self.setMouseTracking(True)
        self.setAlternatingRowColors(True)
        self.setItemDelegate(self.delegate)
        self.setSelectionBehavior(TableWidget.SelectRows)
        self.horizontalHeader().setHighlightSections(False)
        self.verticalHeader().setHighlightSections(False)
        self.verticalHeader().setDefaultSectionSize(38)

        self.entered.connect(lambda i: self._setHoverRow(i.row()))
        self.pressed.connect(lambda i: self._setPressedRow(i.row()))
        self.verticalHeader().sectionClicked.connect(self.selectRow)

    def setBorderVisible(self, isVisible: bool):
        """set the visibility of border"""
        self.setProperty("isBorderVisible", isVisible)
        updateDynamicStyle(self)

    def setBorderRadius(self, radius: int):
        """set the radius of border"""
        qss = f"QTableView{{border-radius: {radius}px}}"
        setCustomStyleSheet(self, qss, qss)

    def setCheckedColor(self, light, dark):
        """set the color in checked status

        Parameters
        ----------
        light, dark: str | QColor | Qt.GlobalColor
            color in light/dark theme mode
        """
        self.delegate.setCheckedColor(light, dark)

    def _setHoverRow(self, row: int):
        """set hovered row"""
        self.delegate.setHoverRow(row)
        self.viewport().update()

    def _setPressedRow(self, row: int):
        """set pressed row"""
        if self.selectionMode() == QTableView.SelectionMode.NoSelection:
            return

        self.delegate.setPressedRow(row)
        self.viewport().update()

    def _setSelectedRows(self, indexes: List[QModelIndex]):
        if self.selectionMode() == QTableView.SelectionMode.NoSelection:
            return

        self.delegate.setSelectedRows(indexes)
        self.viewport().update()

    def leaveEvent(self, e):
        QTableView.leaveEvent(self, e)
        self._setHoverRow(-1)

    def resizeEvent(self, e):
        QTableView.resizeEvent(self, e)
        self.viewport().update()

    def keyPressEvent(self, e: QKeyEvent):
        QTableView.keyPressEvent(self, e)
        self.updateSelectedRows()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton or self._isSelectRightClickedRow:
            return QTableView.mousePressEvent(self, e)

        index = self.indexAt(e.pos())
        if index.isValid():
            self._setPressedRow(index.row())

        QWidget.mousePressEvent(self, e)

    def mouseReleaseEvent(self, e):
        QTableView.mouseReleaseEvent(self, e)
        self.updateSelectedRows()

        if self.indexAt(e.pos()).row() < 0 or e.button() == Qt.RightButton:
            self._setPressedRow(-1)

    def setItemDelegate(self, delegate: TableItemDelegate):
        self.delegate = delegate
        super().setItemDelegate(delegate)

    def selectAll(self):
        QTableView.selectAll(self)
        self.updateSelectedRows()

    def selectRow(self, row: int):
        QTableView.selectRow(self, row)
        self.updateSelectedRows()

    def clearSelection(self):
        QTableView.clearSelection(self)
        self.updateSelectedRows()

    def setCurrentIndex(self, index: QModelIndex):
        QTableView.setCurrentIndex(self, index)
        self.updateSelectedRows()

    def updateSelectedRows(self):
        self._setSelectedRows(self.selectedIndexes())


class TableWidget(TableBase, QTableWidget):
    """Table widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        updateDynamicStyle(self)

    def setCurrentCell(self, row: int, column: int, command=None):
        self.setCurrentItem(self.item(row, column), command)

    def setCurrentItem(self, item: QTableWidgetItem, command=None):
        if not command:
            super().setCurrentItem(item)
        else:
            super().setCurrentItem(item, command)

        self.updateSelectedRows()

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(
        bool, isSelectRightClickedRow, setSelectRightClickedRow
    )


class TableView(TableBase, QTableView):
    """Table view"""

    def __init__(self, parent=None):
        super().__init__(parent)
        updateDynamicStyle(self)

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(
        bool, isSelectRightClickedRow, setSelectRightClickedRow
    )


class RoundTableBase:
    """Round table base class - no header, no border, taller rows"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide header
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        # No border
        self.setBorderVisible(False)

        # Taller rows (default 38 -> 48)
        self.verticalHeader().setDefaultSectionSize(48)

        # No selection indicator, larger border radius, StackedWidget style
        self.delegate.setShowIndicator(False)
        self.delegate.setBorderRadius(8)
        self.delegate.setUseStackedWidgetStyle(True)


class RoundTableWidget(RoundTableBase, TableWidget):
    """Round table widget"""

    def __init__(self, parent=None):
        super().__init__(parent)


class RoundTableView(RoundTableBase, TableView):
    """Round table view"""

    def __init__(self, parent=None):
        super().__init__(parent)


class LineTableBase:
    """Line table base class - has header, no border, no alternating rows"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide vertical header only
        self.verticalHeader().hide()

        # No border
        self.setBorderVisible(False)

        # Set isLineTable property for QSS styling
        self.setProperty("isLineTable", True)

        # Taller header (default 38 -> 48)
        self.horizontalHeader().setFixedHeight(52)
        self.horizontalHeader().setStretchLastSection(False)

        # Taller rows (default 38 -> 48)
        self.verticalHeader().setDefaultSectionSize(48)

        # No alternating row colors
        self.setAlternatingRowColors(False)

        # No selection indicator, no border radius, theme color selection, show divider
        self.delegate.setShowIndicator(False)
        self.delegate.setBorderRadius(0)
        self.delegate.setUseThemeColorSelection(True)
        self.delegate.setShowRowDivider(True)
        self.delegate.margin = 0


class LineTableWidget(LineTableBase, TableWidget):
    """Line table widget"""

    def __init__(self, parent=None):
        super().__init__(parent)


class LineTableView(LineTableBase, TableView):
    """Line table view"""

    def __init__(self, parent=None):
        super().__init__(parent)
