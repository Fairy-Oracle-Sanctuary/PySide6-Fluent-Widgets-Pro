"""Run with py -3.9 tests/check_image_magnifier.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QColor, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import ImageMagnifierWidget, Theme, setTheme, setThemeColor


def run():
    app = QApplication([])
    source = QImage(400, 300, QImage.Format_RGB32)
    source.fill(Qt.white)
    painter = QPainter(source)
    painter.fillRect(200, 0, 200, 300, QColor(Qt.red))
    painter.end()
    widget = ImageMagnifierWidget(source)
    widget.scaledToWidth(200)
    widget.show()
    widget.setFocus()
    app.processEvents()
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        setThemeColor('#8764b8')
        QTest.mouseMove(widget, QPoint(90, 75))
        QTest.qWait(20)
        QTest.mouseMove(widget, QPoint(100, 75))
        QTest.qWait(30)
        image = widget.grab().toImage()
        assert image.pixelColor(110, 85).red() > 240
        widget.setMagnifierEnabled(False)
        assert not widget.isMagnifierEnabled()
        widget.setMagnifierEnabled(True)
        widget.setMagnification(3)
        widget.setRadius(40)
        assert widget.magnification() == 3 and widget.radius() == 40
        previous_x = widget._position.x()
        QTest.keyClick(widget, Qt.Key_Right)
        assert widget._position.x() == min(widget.width(), previous_x + 5)
    for bad in (0, float('nan'), float('inf')):
        try:
            widget.setMagnification(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid zoom accepted')
    widget.setImage(QImage())
    widget.grab()
    widget.close()
    print('PASS: image input, scaling, lens, zoom, radius, keyboard and themes')


if __name__ == '__main__':
    run()
