"""Image cropping editor with draggable selection and customizable clip paths."""
from enum import Enum

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap, QTransform
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from ...common.icon import FluentIcon, Theme


_CROP_MASK_COLOR = QColor(0, 0, 0, 170)


class CropShape(Enum):
    RECTANGLE = 0
    CIRCLE = 1
    CUSTOM = 2


class _CropCanvas(QWidget):
    selectionChanged = Signal(QRectF)

    def __init__(self, parent):
        super().__init__(parent)
        self.image = QImage()
        self.selection = QRectF()
        self.shape = CropShape.RECTANGLE
        self.pathFactory = None
        self._drag = None
        self.setMinimumSize(200, 160)
        self.setMouseTracking(True)

    def imageRect(self):
        if self.image.isNull():
            return QRectF()
        scale = min((self.width() - 40) / self.image.width(),
                    (self.height() - 40) / self.image.height())
        w, h = self.image.width() * scale, self.image.height() * scale
        return QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h)

    def setImage(self, image):
        self.image = QImage(image)
        self.selection = QRectF(self.image.rect())
        if not self.image.isNull():
            self.selection.adjust(self.image.width() * .1, self.image.height() * .1,
                                  -self.image.width() * .1, -self.image.height() * .1)
        self.update()

    def displaySelection(self):
        rect = self.imageRect()
        if rect.isEmpty():
            return QRectF()
        s = rect.width() / self.image.width()
        return QRectF(rect.x() + self.selection.x() * s,
                      rect.y() + self.selection.y() * s,
                      self.selection.width() * s, self.selection.height() * s)

    def cropPath(self, rect):
        if self.shape == CropShape.CUSTOM and self.pathFactory:
            return self.pathFactory(QRectF(rect))
        path = QPainterPath()
        if self.shape == CropShape.CIRCLE:
            side = min(rect.width(), rect.height())
            circle = QRectF(0, 0, side, side)
            circle.moveCenter(rect.center())
            path.addEllipse(circle)
        else:
            path.addRect(rect)
        return path

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or self.image.isNull():
            return super().mousePressEvent(event)
        rect = self.displaySelection()
        corners = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
        handle = next((i for i, p in enumerate(corners)
                       if (p - event.position()).manhattanLength() <= 16), None)
        if handle is not None or rect.contains(event.position()):
            self._drag = (handle, event.position(), QRectF(self.selection))
            event.accept()

    def mouseMoveEvent(self, event):
        if not self._drag:
            return super().mouseMoveEvent(event)
        handle, origin, initial = self._drag
        scale = self.imageRect().width() / self.image.width()
        delta = (event.position() - origin) / scale
        rect = QRectF(initial)
        bounds = QRectF(self.image.rect())
        if handle is None:
            rect.translate(delta)
            rect.moveLeft(max(0, min(rect.x(), bounds.width() - rect.width())))
            rect.moveTop(max(0, min(rect.y(), bounds.height() - rect.height())))
        else:
            minimum = min(16 / scale, initial.width(), initial.height())
            if handle in (0, 3):
                rect.setLeft(max(0, min(initial.left() + delta.x(), initial.right() - minimum)))
            else:
                rect.setRight(min(bounds.right(), max(initial.right() + delta.x(), initial.left() + minimum)))
            if handle in (0, 1):
                rect.setTop(max(0, min(initial.top() + delta.y(), initial.bottom() - minimum)))
            else:
                rect.setBottom(min(bounds.bottom(), max(initial.bottom() + delta.y(), initial.top() + minimum)))
            if self.shape == CropShape.CIRCLE:
                side = min(rect.width(), rect.height())
                anchor = (initial.bottomRight(), initial.bottomLeft(),
                          initial.topLeft(), initial.topRight())[handle]
                rect = QRectF(0, 0, side, side)
                if handle == 0:
                    rect.moveBottomRight(anchor)
                elif handle == 1:
                    rect.moveBottomLeft(anchor)
                elif handle == 2:
                    rect.moveTopLeft(anchor)
                else:
                    rect.moveTopRight(anchor)
        self.selection = rect
        self.selectionChanged.emit(QRectF(rect))
        self.update()

    def mouseReleaseEvent(self, event):
        self._drag = None
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        if self.image.isNull():
            return
        rect = self.imageRect()
        # Transparent source pixels must not reveal the gallery underneath.
        # Back only the image bounds with neutral gray, never the whole canvas.
        painter.fillRect(rect, QColor(92, 92, 92))
        painter.drawImage(rect, self.image, QRectF(self.image.rect()))
        selection = self.displaySelection()
        mask = QPainterPath()
        mask.addRect(rect)
        mask = mask.subtracted(self.cropPath(selection))
        painter.fillPath(mask, _CROP_MASK_COLOR)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        for point in (selection.topLeft(), selection.topRight(),
                      selection.bottomLeft(), selection.bottomRight()):
            painter.drawEllipse(point, 8, 8)


class _CropToolButton(QPushButton):
    def __init__(self, symbol, label, parent):
        super().__init__(parent)
        self.symbol = symbol
        self.setFixedSize(46, 40)
        self.setAccessibleName(label)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.underMouse() and self.isEnabled():
            painter.save()
            painter.translate(2, 2)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 12 if self.isDown() else 18))
            if self.symbol in ('cancel', 'accept'):
                # Large outer corners follow the toolbar; inner corners stay
                # compact next to the separators.
                w, h = self.width() - 4, self.height() - 4
                w -= 2
                if self.symbol == 'accept':
                    painter.translate(2, 0)
                left, right = (16, 4) if self.symbol == 'cancel' else (4, 16)
                path = QPainterPath()
                path.moveTo(left, 0)
                path.lineTo(w - right, 0)
                path.quadTo(w, 0, w, right)
                path.lineTo(w, h - right)
                path.quadTo(w, h, w - right, h)
                path.lineTo(left, h)
                path.quadTo(0, h, 0, h - left)
                path.lineTo(0, left)
                path.quadTo(0, 0, left, 0)
                painter.drawPath(path)
            else:
                painter.drawRoundedRect(QRectF(0, 0, self.width() - 4,
                                              self.height() - 4), 6, 6)
            painter.restore()
        painter.setPen(QPen(QColor(255, 255, 255, 255 if self.isEnabled() else 80), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.translate(self.width() / 2, self.height() / 2)
        if self.symbol == 'rotate':
            if not self.isEnabled():
                painter.setOpacity(80 / 255)
            FluentIcon.ROTATE.render(painter, QRectF(-7, -7, 14, 14), Theme.DARK)
            return
        painter.scale(0.72, 0.72)
        if self.symbol == 'cancel':
            painter.drawLine(-7, -7, 7, 7)
            painter.drawLine(-7, 7, 7, -7)
        elif self.symbol == 'accept':
            painter.drawLine(-9, 0, -3, 6)
            painter.drawLine(-3, 6, 10, -7)
        elif self.symbol == 'flip':
            painter.drawLine(0, -9, 0, 9)
            painter.drawLine(3, -8, 10, 8)
            painter.drawLine(10, 8, 3, 8)
            painter.drawLine(3, 8, 3, -8)
            path = QPainterPath()
            path.moveTo(-3, -8)
            path.lineTo(-10, 8)
            path.lineTo(-3, 8)
            path.closeSubpath()
            painter.fillPath(path, Qt.white)
        else:
            pen = painter.pen()
            pen.setStyle(Qt.DotLine)
            painter.setPen(pen)
            painter.drawRect(QRectF(-9, -9, 18, 18))
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(QRectF(-5, -7, 10, 14))


class _CropToolBar(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(36, 36, 36))
        painter.drawRoundedRect(self.rect(), 18, 18)
        painter.setPen(QPen(QColor(255, 255, 255, 65), 1))
        for index in (1, 4):
            x = 4 + index * 52 - 3
            painter.drawLine(x, 11, x, self.height() - 11)


class _CropWindowMask(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), _CROP_MASK_COLOR)


class ImageCropper(QDialog):
    """Non-saving crop dialog; imageCropped returns a QImage on confirmation.

    Custom shapes use setCropPathFactory(callable), taking a QRectF and returning
    a QPainterPath in that rectangle's coordinate system.
    """
    imageCropped = Signal(QImage)

    def __init__(self, image=None, parent=None):
        if parent is not None:
            parent = parent.window()
        super().__init__(parent)
        self.setWindowTitle(self.tr('Crop image'))
        # Same in-window layering as MaskDialogBase. A separate transparent
        # modal window deactivates the Mica host and changes its backdrop.
        self.setWindowFlags(Qt.FramelessWindowHint if parent is not None
                            else Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        if parent is None:
            self.setModal(True)
        self.resize(860, 600)
        self.windowMask = _CropWindowMask(self)
        self.windowMask.resize(self.size())
        self.windowMask.lower()
        self.canvas = _CropCanvas(self)
        self.toolBar = _CropToolBar(self)
        toolbarLayout = QHBoxLayout(self.toolBar)
        toolbarLayout.setContentsMargins(4, 4, 4, 4)
        toolbarLayout.setSpacing(6)
        self.cancelButton = _CropToolButton('cancel', self.tr('Cancel'), self.toolBar)
        self.rotateButton = _CropToolButton('rotate', self.tr('Rotate clockwise'), self.toolBar)
        self.flipButton = _CropToolButton('flip', self.tr('Flip horizontally'), self.toolBar)
        self.shapeButton = _CropToolButton('shape', self.tr('Custom crop shape'), self.toolBar)
        self.yesButton = _CropToolButton('accept', self.tr('Confirm'), self.toolBar)
        self.shapeButton.setEnabled(False)
        for button in (self.cancelButton, self.rotateButton, self.flipButton,
                       self.shapeButton, self.yesButton):
            toolbarLayout.addWidget(button)
        self.editorLayout = QVBoxLayout(self)
        self.editorLayout.setContentsMargins(24, 24, 24, 24)
        self.editorLayout.setSpacing(0)
        self.editorLayout.addWidget(self.canvas, 1)
        self.editorLayout.addSpacing(80)
        self.editorLayout.addWidget(self.toolBar, 0, Qt.AlignHCenter)
        if parent is not None:
            parent.window().installEventFilter(self)
        self.cancelButton.clicked.connect(self.reject)
        self.rotateButton.clicked.connect(self.rotate)
        self.flipButton.clicked.connect(self.flip)
        self.yesButton.clicked.connect(self.accept)
        self.setImage(image)

    def resizeEvent(self, event):
        self.windowMask.resize(self.size())
        super().resizeEvent(event)

    def _syncOwnerGeometry(self):
        owner = self.parentWidget()
        if owner is None:
            return
        owner = owner.window()
        self.setGeometry(owner.rect())
        self.editorLayout.setContentsMargins(
            round(owner.width() * .07), round(owner.height() * .12),
            round(owner.width() * .07), 24)

    def showEvent(self, event):
        self._syncOwnerGeometry()
        self.raise_()
        super().showEvent(event)

    def eventFilter(self, obj, event):
        if self.isVisible() and event.type() in (QEvent.Move, QEvent.Resize):
            self._syncOwnerGeometry()
        return super().eventFilter(obj, event)

    def setImage(self, image):
        if isinstance(image, QPixmap):
            image = image.toImage()
        elif not isinstance(image, QImage):
            image = QImage(str(image)) if image is not None else QImage()
        self.canvas.setImage(image)
        self.setCropShape(self.canvas.shape)
        self.yesButton.setEnabled(not image.isNull())
        self.rotateButton.setEnabled(not image.isNull())
        self.flipButton.setEnabled(not image.isNull())

    def setCropShape(self, shape):
        if not isinstance(shape, CropShape):
            raise TypeError('shape must be a CropShape')
        self.canvas.shape = shape
        if shape == CropShape.CIRCLE:
            selection = self.canvas.selection
            side = min(selection.width(), selection.height())
            square = QRectF(0, 0, side, side)
            square.moveCenter(selection.center())
            self.canvas.selection = square
        self.canvas.update()

    def setCropPathFactory(self, factory):
        if not callable(factory):
            raise TypeError('factory must be callable')
        self.canvas.pathFactory = factory
        self.setCropShape(CropShape.CUSTOM)

    def rotate(self):
        self.canvas.setImage(self.canvas.image.transformed(QTransform().rotate(90)))
        self.setCropShape(self.canvas.shape)

    def flip(self):
        self.canvas.setImage(self.canvas.image.mirrored(True, False))
        self.setCropShape(self.canvas.shape)

    def croppedImage(self):
        rect = self.canvas.selection.toAlignedRect().intersected(self.canvas.image.rect())
        image = self.canvas.image.copy(rect)
        if image.isNull() or self.canvas.shape == CropShape.RECTANGLE:
            return image
        result = QImage(image.size(), QImage.Format_ARGB32_Premultiplied)
        result.fill(Qt.transparent)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipPath(self.canvas.cropPath(QRectF(image.rect())))
        painter.drawImage(0, 0, image)
        painter.end()
        return result

    def accept(self):
        image = self.croppedImage()
        if image.isNull():
            return
        self.imageCropped.emit(image)
        super().accept()
