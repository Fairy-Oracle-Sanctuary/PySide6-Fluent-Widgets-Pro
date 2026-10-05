"""Run with py -3.9 tests/check_image_cropper.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QImage, QPainterPath
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import ImageCropper, CropShape


def run():
    app = QApplication([])
    source = QImage(400, 200, QImage.Format_RGB32)
    source.fill(Qt.red)
    editor = ImageCropper(source)
    editor.show()
    app.processEvents()
    assert not editor.shapeButton.isEnabled()
    assert editor.croppedImage().size().width() == 320
    canvas = editor.canvas
    center = canvas.displaySelection().center().toPoint()
    initial = QRectF(canvas.selection)
    QTest.mousePress(canvas, Qt.LeftButton, pos=center)
    QTest.mouseMove(canvas, center + QPoint(15, 10))
    QTest.qWait(30)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=center + QPoint(15, 10))
    assert canvas.selection != initial
    assert QRectF(canvas.image.rect()).contains(canvas.selection)
    editor.rotate()
    assert canvas.image.width() == 200 and canvas.image.height() == 400
    editor.flip()
    editor.setCropShape(CropShape.CIRCLE)
    circle = editor.croppedImage()
    assert circle.pixelColor(0, 0).alpha() == 0
    assert circle.pixelColor(circle.width() // 2, circle.height() // 2).alpha() == 255
    def custom(rect):
        path = QPainterPath()
        path.addRoundedRect(rect, 20, 20)
        return path
    editor.setCropPathFactory(custom)
    assert editor.croppedImage().pixelColor(0, 0).alpha() == 0
    results = []
    editor.imageCropped.connect(results.append)
    editor.accept()
    assert len(results) == 1
    cancelled = ImageCropper(source)
    cancelled.imageCropped.connect(results.append)
    cancelled.reject()
    assert len(results) == 1
    print('PASS: crop, drag, bounds, rotation, flip, masks, accept and cancel')


if __name__ == '__main__':
    run()
