"""Run with py -3.9 tests/check_interactive_rating.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget
from qfluentwidgets_pro import InteractiveRatingWidget, Theme, setTheme


def move(widget, x):
    pos = QPointF(x, widget.height() / 2)
    QApplication.sendEvent(widget, QMouseEvent(QEvent.MouseMove, pos, pos,
                                               Qt.NoButton, Qt.NoButton, Qt.NoModifier))


def click(widget, x, button=Qt.LeftButton):
    pos = QPointF(x, widget.height() / 2)
    for kind, buttons in ((QEvent.MouseButtonPress, button), (QEvent.MouseButtonRelease, Qt.NoButton)):
        QApplication.sendEvent(widget, QMouseEvent(kind, pos, pos, button, buttons, Qt.NoModifier))


def pixel(image, x, y):
    scale = image.devicePixelRatio()
    return image.pixelColor(round(x * scale), round(y * scale))


def run():
    app = QApplication([])
    owner = QWidget()
    layout = QHBoxLayout(owner)
    rating = InteractiveRatingWidget(3)
    layout.addWidget(rating)
    layout.addStretch()
    owner.show()
    QTest.qWait(20)
    rating.clearFocus()
    assert rating.width() == 116 and rating.height() == 24
    previews, values = [], []
    rating.hovered.connect(previews.append)
    rating.valueChanged.connect(values.append)
    x = 48 + 20 / 3
    move(rating, x)
    assert abs(rating.displayValue() - (2 + 1 / 3)) < 1e-12
    assert abs(rating._fillPosition(rating.displayValue()) - x) < 1e-12
    assert rating.value() == 3 and values == []
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        QTest.qWait(20)
        rating.clearFocus()
        image = rating.grab().toImage()
        color = rating.starColor()
        assert pixel(image, 10, 12) == color and pixel(image, 34, 12) == color
        # At 1x DPI this fractional clip falls on an antialiased star edge.
        sample = pixel(image, x - 1, 12)
        assert max(abs(a - b) for a, b in zip(sample.getRgb(), color.getRgb())) <= 2
        assert pixel(image, x + 1, 12) != color
        assert pixel(image, 58, 12) != color and pixel(image, 82, 12) != color
        for reason in (Qt.MouseFocusReason, Qt.TabFocusReason):
            rating.setFocus(reason)
            QTest.qWait(20)
            assert rating.hasFocus()
            assert rating.grab().toImage() == image, 'Focus must not draw a border around the stars'
            rating.clearFocus()
    for x in (0., 10.1, 19.9, 20., 21.2, 23.99, 24., 24.1, 55.01, 100.3, 115.9, 116.):
        move(rating, x)
        # At a star's end the inverse may span its empty gap; the rendered
        # coverage is identical. Only require inverse equality inside a star.
        if x % 24 < 20:
            assert abs(rating._fillPosition(rating.displayValue()) - x) < 1e-10
    assert rating._valueAt(21) == rating._valueAt(23.9) == 1
    QApplication.sendEvent(rating, QEvent(QEvent.Leave))
    assert rating.displayValue() == rating.value() == 3

    x = 48 + 20 / 3
    click(rating, x)
    assert abs(rating.value() - (2 + 1 / 3)) < 1e-12
    assert len(values) == 1
    move(rating, 10)
    QApplication.sendEvent(rating, QEvent(QEvent.Leave))
    assert rating.displayValue() == rating.value()
    click(rating, 10, Qt.RightButton)
    assert len(values) == 1
    rating.setReadOnly(True)
    move(rating, 100)
    click(rating, 100)
    QTest.keyClick(rating, Qt.Key_End)
    assert len(values) == 1 and rating.displayValue() == rating.value()
    rating.setReadOnly(False)
    QTest.keyClick(rating, Qt.Key_Home)
    assert rating.value() == 0
    QTest.keyClick(rating, Qt.Key_Right)
    assert abs(rating.value() - .1) < 1e-12
    QTest.keyClick(rating, Qt.Key_End)
    assert rating.value() == 5
    rating.setValue(-100)
    assert rating.value() == 0
    rating.setValue(100)
    assert rating.value() == 5
    move(rating, 40)
    rating.setEnabled(False)
    assert rating.displayValue() == rating.value() == 5
    move(rating, 10)
    assert rating.displayValue() == 5
    rating.setEnabled(True)
    rating.setStarColor("#009faa", "#22ddec")
    for theme, color in ((Theme.LIGHT, "#009faa"), (Theme.DARK, "#22ddec")):
        setTheme(theme)
        assert rating.starColor().name() == color
    for invalid in (float("nan"), float("inf")):
        try:
            rating.setValue(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Nonfinite score accepted")
    owner.close()
    print("PASS: fractional cursor positions, pixel clipping, gaps, preview/commit, keyboard, read-only, themes, values and no focus border")


if __name__ == "__main__":
    run()
