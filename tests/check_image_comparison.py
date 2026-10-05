"""Run with py -3.9 tests/check_image_comparison.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import ImageComparisonSlider


def run():
    app = QApplication([])
    left = QImage(200, 150, QImage.Format_RGB32)
    right = QImage(200, 150, QImage.Format_RGB32)
    left.fill(Qt.red)
    right.fill(Qt.blue)
    widget = ImageComparisonSlider(left, right)
    widget.scaledToWidth(200)
    widget.show()
    app.processEvents()
    for value in (0, 25, 50, 75, 100):
        widget.setValue(value)
        image = widget.grab().toImage()
        scale = image.devicePixelRatio()
        if value >= 25:
            assert image.pixelColor(round(10 * scale), round(10 * scale)) == QColor(Qt.red)
        if value <= 75:
            assert image.pixelColor(round(190 * scale), round(10 * scale)) == QColor(Qt.blue)
    QTest.mousePress(widget, Qt.LeftButton, pos=QPoint(50, 70))
    QTest.mouseRelease(widget, Qt.LeftButton, pos=QPoint(150, 70))
    assert widget.value() == 75
    QTest.keyClick(widget, Qt.Key_Left)
    assert widget.value() == 74
    QTest.keyClick(widget, Qt.Key_Home)
    assert widget.value() == 0
    QTest.keyClick(widget, Qt.Key_End)
    assert widget.value() == 100
    widget.setValue(-5)
    assert widget.value() == 0
    widget.setImages(None, None)
    widget.grab()
    widget.close()
    print('PASS: image clipping, endpoints, dragging, keyboard and empty images')


if __name__ == '__main__':
    run()
