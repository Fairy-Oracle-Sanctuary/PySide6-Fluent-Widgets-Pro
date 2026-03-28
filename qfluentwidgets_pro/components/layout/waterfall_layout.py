# coding:utf-8

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import QLayout, QWidgetItem


class WaterfallLayout(QLayout):
    """Waterfall layout - multi-column layout with equal width and variable height

    Items are placed into the shortest column to minimize vertical gaps.
    Suitable for image galleries, card layouts, etc.
    """

    def __init__(self, parent=None, needAni=False, isTight=False):
        """
        Parameters
        ----------
        parent:
            parent window or layout

        needAni: bool
            whether to add moving animation

        isTight: bool
            whether to use the tight layout when widgets are hidden
        """
        super().__init__(parent)
        self._items = []  # type: List[QLayoutItem]
        self._anis = []  # type: List[QPropertyAnimation]
        self._aniGroup = QParallelAnimationGroup(self)
        self._verticalSpacing = 5
        self._horizontalSpacing = 10
        self._columnCount = 3  # default column count
        self._columnWidth = 0  # 0 means auto calculate based on available width
        self._fixedColumnWidth = 0  # fixed column width, 0 means use _columnWidth
        self.duration = 300
        self.ease = QEasingCurve.Linear
        self.needAni = needAni
        self.isTight = isTight
        self._deBounceTimer = QTimer(self)
        self._deBounceTimer.setSingleShot(True)
        self._deBounceTimer.timeout.connect(
            lambda: self._doLayout(self.geometry(), True)
        )
        self._wParent = None
        self._isInstalledEventFilter = False

    def addItem(self, item):
        self._items.append(item)

    def insertItem(self, index, item):
        self._items.insert(index, item)

    def addWidget(self, w):
        super().addWidget(w)
        self._onWidgetAdded(w)

    def insertWidget(self, index, w):
        self.insertItem(index, QWidgetItem(w))
        self.addChildWidget(w)
        self._onWidgetAdded(w, index)

    def _onWidgetAdded(self, w, index=-1):
        if not self._isInstalledEventFilter:
            if w.parent():
                self._wParent = w.parent()
                w.parent().installEventFilter(self)
            else:
                w.installEventFilter(self)

        if not self.needAni:
            return

        ani = QPropertyAnimation(w, b"geometry")
        ani.setEndValue(QRect(QPoint(0, 0), w.size()))
        ani.setDuration(self.duration)
        ani.setEasingCurve(self.ease)
        w.setProperty("waterfallAni", ani)
        self._aniGroup.addAnimation(ani)

        if index == -1:
            self._anis.append(ani)
        else:
            self._anis.insert(index, ani)

    def setAnimation(self, duration, ease=QEasingCurve.Linear):
        """set the moving animation

        Parameters
        ----------
        duration: int
            the duration of animation in milliseconds

        ease: QEasingCurve
            the easing curve of animation
        """
        if not self.needAni:
            return

        self.duration = duration
        self.ease = ease

        for ani in self._anis:
            ani.setDuration(duration)
            ani.setEasingCurve(ease)

    def count(self):
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]

        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            item = self._items[index]  # type: QLayoutItem
            ani = item.widget().property("waterfallAni")
            if ani:
                self._anis.remove(ani)
                self._aniGroup.removeAnimation(ani)
                ani.deleteLater()

            return self._items.pop(index).widget()

        return None

    def removeWidget(self, widget):
        for i, item in enumerate(self._items):
            if item.widget() is widget:
                return self.takeAt(i)

    def removeAllWidgets(self):
        """remove all widgets from layout"""
        while self._items:
            self.takeAt(0)

    def takeAllWidgets(self):
        """remove all widgets from layout and delete them"""
        while self._items:
            w = self.takeAt(0)
            if w:
                w.deleteLater()

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width: int):
        """get the minimal height according to width"""
        return self._doLayout(QRect(0, 0, width, 0), False)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)

        if self.needAni:
            self._deBounceTimer.start(80)
        else:
            self._doLayout(rect, True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())

        return size

    def setVerticalSpacing(self, spacing: int):
        """set vertical spacing between widgets"""
        self._verticalSpacing = spacing

    def verticalSpacing(self):
        """get vertical spacing between widgets"""
        return self._verticalSpacing

    def setHorizontalSpacing(self, spacing: int):
        """set horizontal spacing between widgets"""
        self._horizontalSpacing = spacing

    def horizontalSpacing(self):
        """get horizontal spacing between widgets"""
        return self._horizontalSpacing

    def setColumnCount(self, count: int):
        """set the number of columns

        Parameters
        ----------
        count: int
            number of columns, set to 0 for auto calculation
        """
        self._columnCount = max(0, count)
        self.invalidate()

    def columnCount(self):
        """get the number of columns"""
        return self._columnCount

    def setColumnWidth(self, width: int):
        """set fixed column width

        Parameters
        ----------
        width: int
            fixed column width, set to 0 to auto calculate
        """
        self._fixedColumnWidth = max(0, width)
        self.invalidate()

    def columnWidth(self):
        """get the fixed column width (0 means auto)"""
        return self._fixedColumnWidth

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if (
            obj in [w.widget() for w in self._items]
            and event.type() == QEvent.Type.ParentChange
        ):
            self._wParent = obj.parent()
            obj.parent().installEventFilter(self)
            self._isInstalledEventFilter = True

        if obj == self._wParent and event.type() == QEvent.Type.Show:
            self._doLayout(self.geometry(), True)
            self._isInstalledEventFilter = True

        return super().eventFilter(obj, event)

    def _calculateColumnCount(self, availableWidth: int):
        """calculate the number of columns based on available width"""
        if self._columnCount > 0:
            return self._columnCount

        # Auto calculate based on minimum item width
        minItemWidth = 150  # default minimum width
        for item in self._items:
            if item.widget() and item.widget().isVisible():
                minItemWidth = max(minItemWidth, item.widget().minimumWidth() or 150)
                break

        spaceX = self.horizontalSpacing()
        count = max(1, (availableWidth + spaceX) // (minItemWidth + spaceX))
        return int(count)

    def _doLayout(self, rect: QRect, move: bool):
        """adjust widgets position using waterfall algorithm"""
        aniRestart = False
        margin = self.contentsMargins()
        availableWidth = rect.width() - margin.left() - margin.right()

        spaceX = self.horizontalSpacing()
        spaceY = self.verticalSpacing()

        # Calculate column count and width
        if self._fixedColumnWidth > 0:
            # Fixed column width mode: calculate column count from available width
            columnWidth = self._fixedColumnWidth
            columnCount = max(1, (availableWidth + spaceX) // (columnWidth + spaceX))
        else:
            # Auto column width mode: use column count setting
            columnCount = self._calculateColumnCount(availableWidth)
            if columnCount <= 0:
                columnCount = 1
            columnWidth = (availableWidth - spaceX * (columnCount - 1)) // columnCount

        # Track the Y position for each column
        columns = [margin.top()] * columnCount

        for i, item in enumerate(self._items):
            if item.widget() and not item.widget().isVisible() and self.isTight:
                continue

            # Find the shortest column
            minCol = 0
            minY = columns[0]
            for col in range(1, columnCount):
                if columns[col] < minY:
                    minY = columns[col]
                    minCol = col

            # Calculate position
            x = rect.x() + margin.left() + minCol * (columnWidth + spaceX)
            y = rect.y() + columns[minCol]

            # Use fixed column width
            itemWidth = columnWidth

            # Get actual item height
            widget = item.widget()
            if widget:
                # Check if widget has fixed height (min == max)
                minH = widget.minimumHeight()
                maxH = widget.maximumHeight()
                if minH > 0 and minH == maxH:
                    itemHeight = minH
                else:
                    itemHeight = widget.sizeHint().height()
            else:
                itemHeight = item.sizeHint().height()

            if move:
                target = QRect(QPoint(x, y), QSize(itemWidth, itemHeight))
                if not self.needAni:
                    item.setGeometry(target)
                elif target != self._anis[i].endValue():
                    self._anis[i].stop()
                    self._anis[i].setEndValue(target)
                    aniRestart = True

            # Update column Y position
            columns[minCol] += itemHeight + spaceY

        if self.needAni and aniRestart:
            self._aniGroup.stop()
            self._aniGroup.start()

        # Return total height (tallest column)
        return max(columns) + margin.bottom() - rect.y()
