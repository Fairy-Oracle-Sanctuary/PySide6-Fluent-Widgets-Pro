"""Browser-like tab silhouettes with the existing TabBar interaction model."""

from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout

from ...common.style_sheet import isDarkTheme
from ...common.icon import drawIcon
from .tab_view import TabBar, TabItem


class _RoundTabLayout(QHBoxLayout):
    """Share adjacent 5px corner wings without shrinking the browser silhouette."""

    OVERLAP = 5

    def __init__(self):
        super().__init__()
        self._actualGeometry = QRect()

    def _visibleItems(self):
        return [self.itemAt(i) for i in range(self.count()) if not self.itemAt(i).isEmpty()]

    def _overlapWidth(self):
        return max(0, len(self._visibleItems()) - 1) * self.OVERLAP

    def sizeHint(self):
        size = super().sizeHint()
        size.setWidth(max(0, size.width() - self._overlapWidth()))
        return size

    def minimumSize(self):
        size = super().minimumSize()
        size.setWidth(max(0, size.width() - self._overlapWidth()))
        return size

    def maximumSize(self):
        size = super().maximumSize()
        size.setWidth(max(0, size.width() - self._overlapWidth()))
        return size

    def geometry(self):
        return QRect(self._actualGeometry)

    def setGeometry(self, rect):
        self._actualGeometry = QRect(rect)
        expanded = QRect(rect)
        expanded.setWidth(rect.width() + self._overlapWidth())
        super().setGeometry(expanded)
        x = rect.x() + self.contentsMargins().left()
        for item in self._visibleItems():
            geometry = item.geometry()
            geometry.moveLeft(x)
            item.setGeometry(geometry)
            x += geometry.width() - self.OVERLAP


class RoundTabItem(TabItem):
    """A top-rounded tab with outward bottom corners and no bottom outline."""

    def _postInit(self):
        super()._postInit()
        self.setFixedHeight(32)
        self.setBorderRadius(8)
        self.setShadowEnabled(False)

    def sizeHint(self):
        return QSize(self.maximumWidth(), 32)

    def setShadowEnabled(self, enabled):
        super().setShadowEnabled(enabled)
        self.shadowEffect.setEnabled(enabled)

    def _selectedPath(self, outline=False, bottom=None):
        width, height = self.width(), self.height()
        height = height if bottom is None else bottom
        edge = .5 if outline else 0
        width -= edge * 2
        radius = max(0, min(self.borderRadius, height / 2, width / 4))
        wing = min(5, radius)
        path = QPainterPath()
        path.moveTo(edge, height)
        if wing:
            path.arcTo(QRectF(edge - wing, height - 2 * wing, 2 * wing, 2 * wing), 270, 90)
        path.lineTo(edge + wing, edge + radius)
        path.quadTo(edge + wing, edge, edge + wing + radius, edge)
        path.lineTo(edge + width - wing - radius, edge)
        path.quadTo(edge + width - wing, edge, edge + width - wing, edge + radius)
        path.lineTo(edge + width - wing, height - wing)
        if wing:
            path.arcTo(QRectF(edge + width - wing, height - 2 * wing, 2 * wing, 2 * wing), 180, 90)
        else:
            path.lineTo(edge + width, height)
        if not outline:
            path.closeSubpath()
        return path

    def _drawSelectedBackground(self, painter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.darkSelectedBackgroundColor if isDarkTheme() else self.lightSelectedBackgroundColor)
        painter.drawPath(self._selectedPath())
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 18) if isDarkTheme() else QColor(0, 0, 0, 15), 1))
        # Open path: outline the top and sides without adding a bottom seam.
        painter.drawPath(self._selectedPath(outline=True))

    def _drawNotSelectedBackground(self, painter):
        if not (self.isPressed or self.isHover):
            return
        shade = 255 if isDarkTheme() else 0
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(shade, shade, shade, 12 if self.isPressed else 10))
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height() - 2),
                                self.borderRadius, self.borderRadius)

    def paintEvent(self, event):
        # Reuse TabItem's text formatting; center icons in the shorter 32px tab.
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if self.isSelected:
            self._drawSelectedBackground(painter)
        else:
            self._drawNotSelectedBackground(painter)
        if not self.isEnabled():
            painter.setOpacity(.4)
        elif not self.isSelected:
            painter.setOpacity(.79 if isDarkTheme() else .61)
        drawIcon(self._icon, painter, QRectF(10, 8, 16, 16))
        self._drawText(painter)


class RoundTabBar(TabBar):
    """Style variant of TabBar; all route, add/close/drag/scroll APIs are inherited.

    Use a zero-spacing layout below this 38px bar and match the content background
    to setTabSelectedBackgroundColor(light, dark) for a continuous browser-like edge.
    Add/close buttons emit requests; the application owns adding/removing pages.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        originalLayout = self.itemLayout
        self.hBoxLayout.removeItem(originalLayout)
        originalLayout.deleteLater()
        self.itemLayout = _RoundTabLayout()
        self.hBoxLayout.insertLayout(0, self.itemLayout)
        self.itemLayout.setSizeConstraint(QHBoxLayout.SetMinAndMaxSize)
        self.setFixedHeight(38)
        self.setTabMaximumWidth(200)
        self.setTabShadowEnabled(False)
        self.itemLayout.setContentsMargins(16, 6, 0, 0)
        self.itemLayout.setSpacing(0)
        self.itemLayout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

    def _createTabItem(self, text, icon):
        return RoundTabItem(text, self.view, icon)

    def setTabMaximumWidth(self, width):
        super().setTabMaximumWidth(width)
        if self.isScrollable():
            # Scrollable tabs use fixed maximum widths, also after editing the
            # maximum-width setting while scrolling is already enabled.
            self.setScrollable(True)

    def isTabVisible(self, index):
        item = self.tabItem(index)
        return item is not None and not item.isHidden()

    def tabRect(self, index):
        item = self.tabItem(index)
        if item is None:
            return None
        x = self.itemLayout.geometry().x() + self.itemLayout.contentsMargins().left()
        for previous in self.items[:index]:
            if not previous.isHidden():
                x += previous.width() - _RoundTabLayout.OVERLAP
        rect = item.geometry()
        rect.moveLeft(x)
        return rect

    def mouseMoveEvent(self, event):
        # TabBar forwards item mouse moves to its reorder logic; a plain hover
        # must never become a drag when the movable switch is enabled.
        if event.buttons() & Qt.LeftButton:
            super().mouseMoveEvent(event)
        else:
            event.ignore()

    def wheelEvent(self, event):
        if self.isScrollable():
            super().wheelEvent(event)
        else:
            event.ignore()

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        painter.setPen(QColor(255, 255, 255, 21) if isDarkTheme() else QColor(0, 0, 0, 15))
        visible = [item for item in self.items if not item.isHidden()]
        for index, item in enumerate(visible):
            following = visible[index + 1] if index + 1 < len(visible) else None
            if item.isHover or item.isSelected or following is not None and (following.isHover or following.isSelected):
                continue
            # Map the separator into viewport coordinates as the view scrolls.
            x = item.mapTo(self.viewport(), QPoint(item.width() - 1, 0)).x()
            y = self.height() // 2 - 8
            painter.drawLine(x, y, x, y + 16)
