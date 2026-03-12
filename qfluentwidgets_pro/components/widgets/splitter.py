# coding:utf-8
"""Splitter widget with fluent style"""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSplitter, QSplitterHandle

from ...common.style_sheet import isDarkTheme


class SplitterHandle(QSplitterHandle):
    """Splitter handle with fluent style"""

    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.isHover: bool = False

    def enterEvent(self, event):
        self.isHover = True
        self.update()

    def leaveEvent(self, event):
        self.isHover = False
        self.update()

    def sizeHint(self):
        if self.orientation() == Qt.Horizontal:
            return QSize(14, 0)
        else:
            return QSize(0, 14)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())

        if isDarkTheme():
            pc = 161
            fc = 42
        else:
            pc = 129
            fc = 229

        painter.setBrush(QColor(pc, pc, pc))
        painter.setPen(Qt.NoPen)

        # Draw hover background
        if self.isHover:
            painter.setBrush(QColor(fc, fc, fc))
            painter.drawRoundedRect(rect, 7, 7)

        # Draw handle indicator
        painter.setBrush(QColor(pc, pc, pc))
        if self.orientation() == Qt.Orientation.Horizontal:
            h = rect.height() // 2 - 16
            painter.drawRoundedRect(rect.adjusted(4.2, h, -4.2, -h), 4, 4)
        else:
            w = rect.width() // 2 - 16
            painter.drawRoundedRect(rect.adjusted(w, 4.4, -w, -4.4), 4, 4)


class Splitter(QSplitter):
    """Splitter with fluent style handle"""

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def createHandle(self):
        return SplitterHandle(self.orientation(), self)
