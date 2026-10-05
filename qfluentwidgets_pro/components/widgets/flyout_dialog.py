"""Custom flyout content with a compact confirmation footer."""
from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QApplication, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from ...common.icon import FluentIcon
from ...common.style_sheet import isDarkTheme
from .button import TransparentToolButton
from .flyout import Flyout, FlyoutAnimationType, FlyoutViewBase
from .label import BodyLabel, SubtitleLabel


class _DialogFlyout(Flyout):
    """Dismiss outside presses explicitly, including native popup mouse grabs."""

    def showEvent(self, event):
        QApplication.instance().installEventFilter(self)
        super().showEvent(event)

    def _outsideView(self, event):
        position = self.view.mapFromGlobal(event.globalPosition().toPoint())
        return not self.view.rect().contains(position)

    def eventFilter(self, watched, event):
        if (self.isVisible() and event.type() == QEvent.MouseButtonPress
                and self._outsideView(event)):
            self.close()
            return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if self._outsideView(event):
            self.close()
            event.accept()
        else:
            super().mousePressEvent(event)

    def closeEvent(self, event):
        QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)


class FlyoutDialog(FlyoutViewBase):
    """A FlyoutViewBase with customizable content and accept/reject actions.

    Use showAt(target) or Flyout.make(dialog, target, parent).
    """

    accepted = Signal()
    rejected = Signal()
    closed = Signal()

    def __init__(self, title='', content='', parent=None):
        super().__init__(parent)
        self._resolved = False
        self._flyout = None
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(1, 1, 1, 1)
        self.vBoxLayout.setSpacing(0)
        self.contentWidget = QWidget(self)
        self.viewLayout = QVBoxLayout(self.contentWidget)
        # Together with the outer 1px border inset, text starts 16px from the edge.
        self.viewLayout.setContentsMargins(15, 15, 15, 15)
        self.viewLayout.setSpacing(8)
        self.titleLabel = SubtitleLabel(title, self.contentWidget)
        self.contentLabel = BodyLabel(content, self.contentWidget)
        self.contentLabel.setWordWrap(True)
        self.titleLabel.setVisible(bool(title))
        self.contentLabel.setVisible(bool(content))
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentLabel)
        self.buttonBar = QWidget(self)
        self.buttonBar.setFixedHeight(40)
        self.buttonLayout = QHBoxLayout(self.buttonBar)
        self.buttonLayout.setContentsMargins(4, 4, 4, 4)
        self.buttonLayout.setSpacing(0)
        self.yesButton = TransparentToolButton(FluentIcon.ACCEPT, self.buttonBar)
        self.cancelButton = TransparentToolButton(FluentIcon.CLOSE, self.buttonBar)
        for button, name in ((self.yesButton, self.tr('Confirm')),
                             (self.cancelButton, self.tr('Cancel'))):
            button.setIconSize(QSize(16, 16))
            button.setAccessibleName(name)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.buttonLayout.addWidget(button, 1)
        self.vBoxLayout.addWidget(self.contentWidget)
        self.vBoxLayout.addWidget(self.buttonBar)
        self.setMinimumWidth(256)
        self.yesButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

    def addWidget(self, widget, stretch=0, align=Qt.AlignLeft):
        self.viewLayout.addWidget(widget, stretch, align)

    def sizeHint(self):
        hint = super().sizeHint()
        margins = self.viewLayout.contentsMargins()
        textWidth = max((self.contentLabel.fontMetrics().horizontalAdvance(line)
                         for line in self.contentLabel.text().splitlines()), default=0)
        # QLabel's wrapped sizeHint assumes a narrow column. Recompute height
        # at the actual popup width; the extra pixel avoids CJK rounding wraps.
        width = max(self.minimumWidth(), hint.width(),
                    min(480, textWidth + margins.left() + margins.right() + 3))
        height = self.vBoxLayout.totalHeightForWidth(width)
        return QSize(width, height if height >= 0 else hint.height())

    def borderColor(self):
        return QColor(255, 255, 255, 20) if isDarkTheme() else super().borderColor()

    def accept(self):
        self._finish(True)

    def reject(self):
        self._finish(False)

    def _finish(self, accepted):
        if self._resolved:
            return
        self._resolved = True
        (self.accepted if accepted else self.rejected).emit()
        self.closed.emit()

    def showAt(self, target, parent=None, aniType=FlyoutAnimationType.PULL_UP):
        self._resolved = False
        self._flyout = _DialogFlyout.make(self, target, parent, aniType)
        self.closed.connect(self._flyout.close)
        self._flyout.closed.connect(self._dismissed)
        return self._flyout

    def _dismissed(self):
        if not self._resolved:
            self.reject()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        color = QColor(255, 255, 255, 15) if isDarkTheme() else QColor(0, 0, 0, 17)
        painter.fillRect(1, self.buttonBar.y(), self.width() - 2, 2, color)
