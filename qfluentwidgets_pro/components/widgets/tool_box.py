"""Native exclusive accordion for arbitrary QWidget tool panels."""

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QEvent, QRect, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QLayout, QSizePolicy, QVBoxLayout, QWidget

from ...common.font import getFont
from ...common.icon import drawIcon
from ...common.style_sheet import isDarkTheme
from .card_widget import SimpleCardWidget


class _ToolBoxHeader(QAbstractButton):
    def __init__(self, text, icon, parent):
        super().__init__(parent)
        self._itemIcon = icon
        self._arrowHovered = False
        self._keyboardFocus = False
        self.setMouseTracking(True)
        self.setText(text)
        self.setAccessibleName(text)
        self.setCheckable(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(getFont(14))
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def sizeHint(self):
        iconWidth = 30 if self._itemIcon is not None else 0
        return QSize(self.fontMetrics().horizontalAdvance(self.text()) + 72 + iconWidth, 48)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.click()
            event.accept()
        else:
            super().keyPressEvent(event)

    def arrowRect(self):
        return QRect(self.width() - 37, 9, 30, 30)

    def enterEvent(self, event):
        self._arrowHovered = True
        self.update()
        super().enterEvent(event)

    def mouseMoveEvent(self, event):
        self._arrowHovered = True
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._arrowHovered = False
        self.update()
        super().leaveEvent(event)

    def focusInEvent(self, event):
        self._keyboardFocus = event.reason() in (Qt.TabFocusReason, Qt.BacktabFocusReason, Qt.ShortcutFocusReason)
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._keyboardFocus = False
        self.update()
        super().focusOutEvent(event)

    def mousePressEvent(self, event):
        self._keyboardFocus = False
        self.update()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        dark = isDarkTheme()
        if self.isEnabled() and (self._arrowHovered or self._keyboardFocus):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 12 if self.isDown() else 18) if dark
                             else QColor(0, 0, 0, 10 if self.isDown() else 7))
            painter.drawRoundedRect(self.arrowRect(), 4, 4)
        color = QColor('#ffffff' if dark else '#000000')
        if not self.isEnabled():
            color.setAlpha(90)
        painter.setPen(color)
        left = 18
        if self._itemIcon is not None:
            painter.save()
            painter.setOpacity(1 if self.isEnabled() else .4)
            drawIcon(self._itemIcon, painter, QRect(left, 14, 20, 20))
            painter.restore()
            left += 30
        rect = QRect(left, 0, max(0, self.width() - left - 48), self.height())
        text = self.fontMetrics().elidedText(self.text(), Qt.ElideRight, rect.width())
        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, text)
        painter.setPen(QPen(color, 1.3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        x, y = self.width() - 22, self.height() / 2
        path = QPainterPath()
        path.moveTo(x - 3.5, y + (1.5 if self.isChecked() else -1.5))
        path.lineTo(x, y + (-2 if self.isChecked() else 2))
        path.lineTo(x + 3.5, y + (1.5 if self.isChecked() else -1.5))
        painter.drawPath(path)


class _ToolBoxSeparator(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 55 if isDarkTheme() else 18))


class _ToolBoxItem(SimpleCardWidget):
    transitionFinished = Signal()

    def __init__(self, widget, text, icon, parent):
        super().__init__(parent)
        self._expanded = False
        self._extent = 0.
        self._bodyWidth = -1
        self._refreshing = False
        self._animation = QVariantAnimation(self)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)
        self._animation.valueChanged.connect(self._setExtent)
        self._animation.finished.connect(self._animationFinished)
        self.setBorderRadius(6)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.header = _ToolBoxHeader(text, icon, self)
        self.clipWidget = QWidget(self)
        self.separator = _ToolBoxSeparator(self.clipWidget)
        self.body = QWidget(self.clipWidget)
        self.bodyLayout = QVBoxLayout(self.body)
        self.bodyLayout.setSizeConstraint(QLayout.SetNoConstraint)
        self.bodyLayout.setContentsMargins(12, 12, 12, 12)
        self.bodyLayout.addWidget(widget)
        self.widget = widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.clipWidget)
        self.body.installEventFilter(self)
        self._setExtent(0.)
        self.clipWidget.hide()
        self.body.hide()

    def _naturalExtent(self):
        width = max(0, self.width() - 2)
        height = self.bodyLayout.totalHeightForWidth(width) if self.bodyLayout.hasHeightForWidth() else self.bodyLayout.sizeHint().height()
        return max(self.bodyLayout.minimumSize().height(), height, 24) + 1

    def _setExtent(self, extent):
        self._extent = max(0., float(extent))
        self.clipWidget.setFixedHeight(round(self._extent))
        self.setFixedHeight(50 + round(self._extent))
        width = max(0, self.width() - 2)
        self.separator.setGeometry(0, 0, width, 1)
        self.body.setGeometry(0, 1, width, self._naturalExtent() - 1)
        self.updateGeometry()

    def setExpanded(self, expanded, duration=0):
        if expanded == self._expanded and duration:
            return
        self._expanded = expanded
        self._animation.stop()
        target = self._naturalExtent() if expanded else 0
        if not duration or abs(self._extent - target) < .5:
            self._setExtent(target)
            self.clipWidget.setVisible(expanded)
            self.body.setVisible(expanded)
            return
        self.clipWidget.show()
        self.body.show()
        self._animation.setStartValue(self._extent)
        self._animation.setEndValue(float(target))
        self._animation.setDuration(duration)
        self._animation.start()

    def _animationFinished(self):
        self.clipWidget.setVisible(self._expanded)
        self.body.setVisible(self._expanded)
        self.transitionFinished.emit()

    def _refreshBody(self):
        if self._refreshing:
            return
        self._refreshing = True
        try:
            target = self._naturalExtent()
            width = max(0, self.width() - 2)
            self.body.setGeometry(0, 1, width, target - 1)
            self.separator.setGeometry(0, 0, width, 1)
            if self._expanded:
                if self._animation.state() == QAbstractAnimation.Running:
                    if abs(float(self._animation.endValue()) - target) > .5:
                        remaining = max(1, self._animation.duration() - self._animation.currentTime())
                        self._animation.stop()
                        self._animation.setStartValue(self._extent)
                        self._animation.setEndValue(float(target))
                        self._animation.setDuration(remaining)
                        self._animation.start()
                else:
                    self._setExtent(target)
        finally:
            self._refreshing = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'body') and self.width() != self._bodyWidth:
            self._bodyWidth = self.width()
            self._refreshBody()

    def eventFilter(self, watched, event):
        if watched is getattr(self, 'body', None) and event.type() == QEvent.LayoutRequest:
            self._refreshBody()
        return super().eventFilter(watched, event)


class ToolBox(QWidget):
    """An accordion: close the previous item before animating the next one open.

    First inserted item opens by default. Clicking the active header or using
    setCurrentIndex(-1) collapses all items. Content retains its widget/state.
    Put the toolbox in a ScrollArea if its expanded content exceeds the page.
    """

    currentChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._currentIndex = -1
        self._animationDuration = 200
        self._syncing = False
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(6)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

    def count(self):
        return len(self._items)

    def currentIndex(self):
        return self._currentIndex

    def currentWidget(self):
        return self.widget(self._currentIndex) if self._currentIndex >= 0 else None

    def _item(self, index):
        if not 0 <= index < self.count():
            raise IndexError('Toolbox item index out of range')
        return self._items[index]

    def widget(self, index):
        return self._item(index).widget

    def indexOf(self, widget):
        return next((i for i, item in enumerate(self._items) if item.widget is widget), -1)

    def addItem(self, widget, text, icon=None):
        return self.insertItem(self.count(), widget, text, icon)

    def insertItem(self, index, widget, text, icon=None):
        if not isinstance(widget, QWidget):
            raise TypeError('Toolbox item must be a QWidget')
        if widget is self or widget.isAncestorOf(self) or self.indexOf(widget) >= 0:
            raise ValueError('Toolbox item must be unique and cannot be an ancestor')
        if not 0 <= index <= self.count():
            raise IndexError('Toolbox insertion index out of range')
        text = str(text)
        item = _ToolBoxItem(widget, text, icon, self)
        item.transitionFinished.connect(self._syncPanels)
        item.header.clicked.connect(lambda checked=False, entry=item: self._toggleItem(entry))
        self._items.insert(index, item)
        self.vBoxLayout.insertWidget(index, item)
        widget.show()
        item.show()
        if self.count() == 1:
            self.setCurrentIndex(0)
        elif self._currentIndex >= index:
            self._currentIndex += 1
            self.currentChanged.emit(self._currentIndex)
        return index

    def _toggleItem(self, item):
        index = self._items.index(item)
        self.setCurrentIndex(-1 if index == self._currentIndex else index)

    def setCurrentIndex(self, index):
        if index != -1:
            item = self._item(index)
            if not item.header.isEnabled():
                return
        if index == self._currentIndex:
            return
        self._currentIndex = index
        self._syncPanels()
        self.updateGeometry()
        self.currentChanged.emit(index)

    def _syncPanels(self):
        if self._syncing:
            return
        self._syncing = True
        try:
            for i, item in enumerate(self._items):
                item.header.setChecked(i == self._currentIndex)
                if i != self._currentIndex:
                    item.setExpanded(False, self._animationDuration if self.isVisible() else 0)
            if any(item._extent > 0 for i, item in enumerate(self._items) if i != self._currentIndex):
                return
            if self._currentIndex >= 0:
                self._items[self._currentIndex].setExpanded(True, self._animationDuration if self.isVisible() else 0)
        finally:
            self._syncing = False

    def animationDuration(self):
        return self._animationDuration

    def setAnimationDuration(self, duration):
        duration = int(duration)
        if duration < 0:
            raise ValueError('Toolbox animation duration must be nonnegative')
        self._animationDuration = duration
        if duration == 0:
            self._syncPanels()

    def removeItem(self, index):
        """Detach and hide the page without deleting it; return it for reuse."""
        item = self._item(index)
        oldIndex = self._currentIndex
        self._items.pop(index)
        item._animation.stop()
        self.vBoxLayout.removeWidget(item)
        widget = item.widget
        widget.hide()
        widget.setParent(None)
        item.hide()
        item.deleteLater()
        if oldIndex == index:
            candidates = list(range(index, self.count())) + list(range(index-1, -1, -1))
            newIndex = next((i for i in candidates if self.isItemEnabled(i)), -1)
        else:
            newIndex = oldIndex - 1 if oldIndex > index else oldIndex
        self._currentIndex = newIndex
        self._syncPanels()
        self.updateGeometry()
        if oldIndex != newIndex or oldIndex == index:
            self.currentChanged.emit(newIndex)
        return widget

    def itemText(self, index):
        return self._item(index).header.text()

    def setItemText(self, index, text):
        header = self._item(index).header
        header.setText(str(text))
        header.setAccessibleName(str(text))
        header.updateGeometry()
        header.update()

    def itemIcon(self, index):
        return self._item(index).header._itemIcon

    def setItemIcon(self, index, icon):
        header = self._item(index).header
        header._itemIcon = icon
        header.updateGeometry()
        header.update()

    def itemHeader(self, index):
        """The keyboard-focusable native button for tooltips/accessibility."""
        return self._item(index).header

    def isItemEnabled(self, index):
        return self._item(index).header.isEnabled()

    def setItemEnabled(self, index, enabled):
        item = self._item(index)
        item.header.setEnabled(enabled)
        item.body.setEnabled(enabled)
        if not enabled and index == self._currentIndex:
            nextIndex = next((i for i in range(self.count()) if self.isItemEnabled(i)), -1)
            self.setCurrentIndex(nextIndex)
