"""Run with py -3.9 tests/check_circle_color_picker.py; also test QT_SCALE_FACTOR=2."""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import CircleColorPicker, Theme, setTheme, themeColor
from gallery.view.color_picker_demo import ColorPickerDemo


def render(widget, scale=1, neutral=False):
    QApplication.processEvents()
    widget.layout().activate()
    if neutral:
        for button in widget._buttons:
            button.clearFocus()
            button.setAttribute(Qt.WA_UnderMouse, False)
    image = QImage(widget.width() * scale, widget.height() * scale, QImage.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(scale)
    image.fill(Qt.transparent)
    widget.render(image, QPoint(), renderFlags=QWidget.DrawChildren)
    return image


def pixel(image, x, y):
    scale = image.devicePixelRatio()
    return image.pixelColor(round(x * scale), round(y * scale))


def run():
    app = QApplication([])
    setTheme(Theme.LIGHT)
    accent = QColor(themeColor())
    picker = CircleColorPicker()
    picker.resize(picker.sizeHint())
    picker.show()
    QTest.qWait(10)
    assert picker.sizeHint().width() == 242 and picker.height() == 32
    assert picker.count() == 6 and picker.currentIndex() == 0
    colors, indices = [], []
    picker.colorChanged.connect(lambda color: colors.append(QColor(color)))
    picker.currentIndexChanged.connect(indices.append)
    button = picker._buttons[1]
    QTest.mouseClick(button, Qt.LeftButton, pos=QPoint(16, 16))
    assert picker.currentIndex() == 1 and picker.color() == QColor('#72D6F4')
    assert len(colors) == 1 and indices == [1]
    QTest.mouseClick(button, Qt.LeftButton, pos=QPoint(16, 16))
    assert button.isChecked() and len(colors) == 1 and indices == [1]
    QTest.mouseClick(picker._buttons[4], Qt.RightButton, pos=QPoint(16, 16))
    QTest.mouseClick(picker._buttons[4], Qt.LeftButton, pos=QPoint(1, 1))
    assert picker.currentIndex() == 1
    QTest.mousePress(picker._buttons[4], Qt.LeftButton, pos=QPoint(16, 16))
    QTest.mouseRelease(picker._buttons[4], Qt.LeftButton, pos=QPoint(1, 1))
    assert picker.currentIndex() == 1
    assert all(not b.toolTip() and b.accessibleName() for b in picker._buttons)

    # Palette selection is completely independent of the application accent.
    assert themeColor() == accent
    picker.setColor('#20396C')
    assert picker.currentIndex() == 4 and themeColor() == accent
    picker.setCurrentIndex(0)
    count = len(colors)
    picker.setCurrentIndex(2)  # equal colors at different indices
    assert indices[-1] == 2 and len(colors) == count
    copy = picker.color()
    copy.setRed(0)
    copies = picker.colors()
    copies[2].setBlue(0)
    assert picker.color() == QColor('#4BACF2')

    # Custom palette and mutation validation are atomic.
    picker.setColors(['red', 'green', 'blue'])
    picker.setColor('green')
    picker.setColors(['blue', 'red', 'green'])
    assert picker.currentIndex() == 2 and picker.color() == QColor('green')
    before, selected, signals = picker.colors(), picker.currentIndex(), (len(colors), len(indices))
    for bad in (['blue', 'not-a-color'], [QColor()], ['red', object()], '#FF0000'):
        try:
            picker.setColors(bad)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError('Invalid palette accepted')
        assert picker.colors() == before and picker.currentIndex() == selected
        assert (len(colors), len(indices)) == signals
    for value in (-2, 3, 100, 1.5, True):
        try:
            picker.setCurrentIndex(value)
        except (TypeError, IndexError):
            pass
        else:
            raise AssertionError('Invalid index accepted')
    try:
        picker.setColor('magenta')
    except ValueError:
        pass
    else:
        raise AssertionError('Out-of-palette selection accepted')
    assert picker.colors() == before

    picker.setCurrentIndex(-1)
    assert not picker.color().isValid() and not any(b.isChecked() for b in picker._buttons)
    QTest.mouseClick(picker._buttons[0], Qt.LeftButton, pos=QPoint(16, 16))
    assert picker.currentIndex() == 0
    QTest.keyClick(picker._buttons[0], Qt.Key_Right)
    assert picker.currentIndex() == 1
    QTest.keyClick(picker._buttons[1], Qt.Key_End)
    assert picker.currentIndex() == 2
    QTest.keyClick(picker._buttons[2], Qt.Key_Home)
    assert picker.currentIndex() == 0
    picker.setLayoutDirection(Qt.RightToLeft)
    QTest.keyClick(picker._buttons[0], Qt.Key_Left)
    assert picker.currentIndex() == 1
    picker.setLayoutDirection(Qt.LeftToRight)
    picker.setCurrentIndex(-1)
    QTest.keyClick(picker._buttons[1], Qt.Key_Space)
    assert picker.currentIndex() == 1
    picker.setCurrentIndex(-1)
    QTest.keyClick(picker._buttons[2], Qt.Key_Return)
    assert picker.currentIndex() == 2
    picker.setEnabled(False)
    QTest.mouseClick(picker._buttons[0], Qt.LeftButton, pos=QPoint(16, 16))
    QTest.keyClick(picker._buttons[2], Qt.Key_Home)
    assert picker.currentIndex() == 2
    picker.setEnabled(True)

    # Exact swatch/ring geometry at 1x and 2x, transparent gap/background,
    # and no theme-accent substitution in either light or dark mode.
    picker.setColors(['#F7630C', '#00CC6A', '#8764B8'])
    picker.resize(picker.sizeHint())
    picker.setCurrentIndex(1)
    for button in picker._buttons:
        button.clearFocus()
        button.setAttribute(Qt.WA_UnderMouse, False)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        for scale in (1, 2):
            image = render(picker, scale, neutral=True)
            assert pixel(image, 16, 16) == QColor('#F7630C')
            assert pixel(image, 58, 16) == QColor('#00CC6A')
            assert pixel(image, 100, 16) == QColor('#8764B8')
            assert pixel(image, 42 + 28, 16).alpha() == 0  # swatch/ring gap
            assert pixel(image, 42 + 30, 16).alpha() > 50  # selected outline
            assert pixel(image, 30, 16).alpha() == 0  # no unselected outline
            assert pixel(image, 35, 16).alpha() == 0  # space between targets
            assert pixel(image, 0, 0).alpha() == 0
    setTheme(Theme.LIGHT)
    assert themeColor() == accent
    base = render(picker, neutral=True)
    picker._buttons[0].setAttribute(Qt.WA_UnderMouse, True)
    hover = render(picker)
    assert pixel(base, 16, 16) != pixel(hover, 16, 16)
    assert picker.currentIndex() == 1  # hover never commits
    picker._buttons[0].setDown(True)
    pressed = render(picker)
    assert pixel(pressed, 16, 16) != pixel(hover, 16, 16)
    picker._buttons[0].setDown(False)
    picker._buttons[0].setAttribute(Qt.WA_UnderMouse, False)
    picker.setEnabled(False)
    assert 100 <= pixel(render(picker), 58, 16).alpha() <= 115
    picker.setEnabled(True)
    picker.setColors([QColor(255, 0, 0, 100), 'transparent'])
    picker.resize(picker.sizeHint())
    assert pixel(render(picker), 16, 16).alpha() == 255  # alpha swatch checkerboard
    assert picker.color().alpha() == 100
    picker.setColors([])
    assert picker.count() == 0 and picker.currentIndex() == -1 and not picker.color().isValid()
    picker.addColor('red')
    picker.addColors(color for color in ('green', 'blue'))
    assert picker.count() == 3 and picker.color() == QColor('red')
    # Defensive copies of initial colors, empty construction, positional parent.
    original = QColor('yellow')
    other = CircleColorPicker([original])
    original.setRed(0)
    assert other.color() == QColor('yellow')
    empty = CircleColorPicker([])
    assert empty.currentIndex() == -1 and empty.count() == 0
    assert CircleColorPicker(picker).parentWidget() is picker

    demo = ColorPickerDemo()
    assert demo.picker.currentIndex() == 1
    demo.paletteEdit.setText('#FF4343, #FFB900, #107C10')
    demo._applyPalette()
    assert demo.picker.colors() == [QColor('#FF4343'), QColor('#FFB900'), QColor('#107C10')]
    assert '#ff4343' in demo.colorLabel.text()
    demo.paletteEdit.setText('#FF4343, invalid')
    demo._applyPalette()
    assert demo.picker.count() == 3 and '无效' in demo.messageLabel.text()
    demo.paletteEdit.clear()
    demo._applyPalette()
    assert '未选择' in demo.colorLabel.text()
    demo._resetPalette()
    assert demo.picker.currentIndex() == 1 and demo.picker.count() == 6
    assert themeColor() == accent

    # Native Qt preview matching the reference's compact horizontal row.
    picker.setColors(CircleColorPicker.DEFAULT_COLORS)
    picker.setCurrentIndex(1)
    picker.resize(picker.sizeHint())
    for button in picker._buttons:
        button.clearFocus()
        button.setAttribute(Qt.WA_UnderMouse, False)
    preview = QImage(297, 54, QImage.Format_ARGB32_Premultiplied)
    preview.fill(Qt.white)
    painter = QPainter(preview)
    painter.drawImage(22, 11, render(picker, neutral=True))
    painter.end()
    path = str(Path(tempfile.gettempdir()) / 'codex-circle-color-picker-preview.png')
    assert preview.save(path)
    picker.close()
    demo.close()
    print('PASS: custom palettes, circular hit tests, exclusive selection, signals, atomic validation, '
          'keyboard/RTL, disabled state, alpha colors, 1x/2x pixels, theme independence and gallery')
    print('Preview:', path)


if __name__ == '__main__':
    run()
