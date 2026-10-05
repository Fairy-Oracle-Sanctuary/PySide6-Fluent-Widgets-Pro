"""Clickable avatar using the shared circular ImageCropper editor."""
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QFileDialog

from ...common.icon import FluentIcon, Theme
from .image_cropper import CropShape, ImageCropper
from .label import AvatarWidget


class AvatarPicker(AvatarWidget):
    """AvatarWidget image/radius APIs plus click-to-select and circular crop."""

    imageChanged = Signal(QImage)

    def _postInit(self):
        super()._postInit()
        self._hovered = False
        self._pressed = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(self.tr('Choose avatar'))

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._pressed = event.button() == Qt.LeftButton
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        activate = (self._pressed and event.button() == Qt.LeftButton
                    and self.rect().contains(event.position().toPoint()))
        self._pressed = False
        # Avoid ImageLabel's unconditional clicked emission for other buttons.
        if activate and self.isEnabled():
            self.clicked.emit()
            self.chooseImage()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter) and not event.isAutoRepeat():
            self.chooseImage()
            event.accept()
        else:
            super().keyPressEvent(event)

    def chooseImage(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window(), self.tr('Choose avatar'), '',
            'Images (*.png *.jpg *.jpeg *.bmp *.webp)')
        if path:
            self.cropImage(path)

    def cropImage(self, image):
        """Open the shared editor for a path, QImage or QPixmap."""
        editor = ImageCropper(image, self.window())
        editor.setCropShape(CropShape.CIRCLE)
        editor.imageCropped.connect(self._applyCrop)
        editor.exec()
        editor.deleteLater()

    def _applyCrop(self, image):
        self.setImage(image)
        self.imageChanged.emit(QImage(image))

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._hovered or not self.isEnabled():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 155))
        painter.drawEllipse(QRectF(self.rect()))
        size = min(28, self.width() * .3)
        FluentIcon.CAMERA.render(painter, QRectF((self.width() - size) / 2,
                                (self.height() - size) / 2, size, size), Theme.DARK)
