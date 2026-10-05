"""Run with py -3.9 tests/check_rating_widget.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget
from qfluentwidgets_pro import RatingWidget, Theme, setTheme


def run():
    app = QApplication([])
    owner = QWidget()
    layout = QHBoxLayout(owner)
    rating = RatingWidget(4.5)
    layout.addWidget(rating)
    layout.addStretch()
    owner.show()
    changes = []
    rating.valueChanged.connect(changes.append)
    assert rating.text() == "4.5" and rating.value() == 4.5
    initialWidth = rating.sizeHint().width()
    rating.setValue(123.4)
    QTest.qWait(20)
    assert rating.sizeHint().width() > initialWidth
    assert rating.width() == rating.sizeHint().width()
    rating.setValue(123.4)
    assert changes == [123.4]
    rating.setValue(4.25)
    rating.setDecimals(2)
    assert rating.text() == "4.25" and rating.value() == 4.25
    rating.setDecimals(0)
    assert rating.text() == "4" and rating.value() == 4.25
    rating.setValue(-.01)
    assert rating.text() == "0"
    rating.setDecimals(1)
    rating.setValue(4.5)
    rating.setStarColor("#f88a00", "#ffaa33")
    for theme, color in ((Theme.LIGHT, "#f88a00"), (Theme.DARK, "#ffaa33")):
        setTheme(theme)
        QTest.qWait(20)
        assert rating.starColor().name() == color
        image = rating.grab().toImage()
        scale = image.devicePixelRatio()
        cx = rating.fontMetrics().horizontalAdvance(rating.text()) + 14
        assert image.pixelColor(round(cx * scale), round(rating.height() / 2 * scale)).name() == color
    before = rating.sizeHint()
    font = QFont(rating.font())
    font.setPixelSize(30)
    rating.setFont(font)
    assert rating.sizeHint().width() > before.width()
    for value in (float("inf"), float("-inf"), float("nan")):
        try:
            rating.setValue(value)
        except ValueError:
            pass
        else:
            raise AssertionError("Nonfinite score accepted")
    assert rating.value() == 4.5
    owner.close()
    print("PASS: values, signals, precision, layout resizing, themes, vector star and invalid input")


if __name__ == "__main__":
    run()
