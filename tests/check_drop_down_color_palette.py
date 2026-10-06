"""Native Qt interaction and rendering checks; no screenshots of the desktop."""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QPoint, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import ColorDialog, DropDownColorPalette, DropDownPushButton, Theme, setTheme, themeColor
from gallery.view.color_picker_demo import ColorPickerDemo


def render(widget, scale=1):
    QApplication.processEvents()
    raster = QImage(round(widget.width() * scale), round(widget.height() * scale), QImage.Format_ARGB32_Premultiplied)
    raster.fill(Qt.transparent)
    raster.setDevicePixelRatio(scale)
    widget.render(raster, QPoint(), renderFlags=QWidget.DrawChildren)
    return raster


def run():
    app = QApplication([])
    setTheme(Theme.LIGHT)
    accent = QColor(themeColor())
    owner = QWidget()
    owner.resize(900, 850)
    picker = DropDownColorPalette('#0078D4', owner)
    picker.resize(picker.sizeHint())
    picker.move(400, 40)
    owner.show()
    owner.activateWindow()
    QTest.qWait(30)
    assert picker.sizeHint() == QSize(54, 32) and isinstance(picker, DropDownPushButton)
    assert picker.color() == QColor('#0078D4') and not picker.isAutomatic()
    assert picker.automaticColor() == QColor('black') and not picker.isAlphaEnabled()
    changed, selected, modes = [], [], []
    picker.colorChanged.connect(lambda color: changed.append(QColor(color)))
    picker.colorSelected.connect(lambda color: selected.append(QColor(color)))
    picker.automaticChanged.connect(modes.append)
    copy = picker.color()
    copy.setRed(255)
    assert picker.color() == QColor('#0078D4')
    picker.setColor('red')
    picker.setColor('red')
    assert changed == [QColor('red')] and not selected
    for invalid in ('invalid color', QColor(), object()):
        for setter in (picker.setColor, picker.setAutomaticColor):
            try:
                setter(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError('Invalid color was accepted')
        assert picker.color() == QColor('red') and picker.automaticColor() == QColor('black')
    picker.setAutomatic()
    assert picker.isAutomatic() and picker.color() == QColor('black') and modes == [True]
    picker.setAutomaticColor('#123456')
    assert picker.color() == QColor('#123456') and not selected
    picker.setColor('#0078D4')
    assert not picker.isAutomatic() and modes == [True, False]
    picker.setAutomaticColor('black')

    # Only completed left clicks open; right clicks and canceled presses do not.
    QTest.mouseClick(picker, Qt.RightButton)
    assert picker._flyout is None
    QTest.mousePress(picker, Qt.LeftButton, pos=QPoint(12, 12))
    QTest.mouseRelease(picker, Qt.LeftButton, pos=QPoint(-10, -10))
    assert picker._flyout is None
    QTest.mouseClick(picker, Qt.LeftButton)
    assert picker._flyout is not None
    flyout = picker._flyout
    QTest.qWait(210)
    view = flyout.view
    assert view.size() == QSize(340, 432) and len(view.buttons) == 70
    assert flyout.windowFlags() & Qt.Popup
    assert view.buttons[0].geometry().topLeft() == QPoint(12, 88)
    assert view.buttons[10].geometry().topLeft() == QPoint(12, 128)
    assert view.buttons[-1].geometry().topLeft() == QPoint(300, 344)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        effect = view.graphicsEffect()
        effect.setEnabled(False)
        for scale in (1, 2):
            raster = render(view, scale)
            for button in view.buttons:
                point = button.geometry().center() * scale
                assert raster.pixelColor(point) == button.color
            assert raster.pixelColor(0, 0).alpha() == 0
        effect.setEnabled(True)
        assert picker.color() == QColor('#0078D4')
    setTheme(Theme.LIGHT)
    assert themeColor() == accent
    # Screenshot-like reference rendering from our own widgets only.
    canvas = QImage(505, 640, QImage.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.white)
    canvas.setDevicePixelRatio(1.25)
    painter = QPainter(canvas)
    painter.drawImage(QPoint(175, 8), render(picker, 1.25))
    painter.drawImage(QPoint(17, 36), render(flyout, 1.25))
    painter.end()
    previewPath = str(Path(tempfile.gettempdir()) / 'codex-drop-down-color-palette-preview.png')
    assert canvas.save(previewPath)

    # Navigation changes focus, not the committed color; confirmation closes.
    view.buttons[0].setFocus()
    QTest.keyClick(view.buttons[0], Qt.Key_Right)
    assert view.buttons[1].hasFocus() and picker.color() == QColor('#0078D4')
    QTest.keyClick(view.buttons[1], Qt.Key_Down)
    assert view.buttons[11].hasFocus()
    QTest.keyClick(view.buttons[11], Qt.Key_End)
    assert view.buttons[19].hasFocus()
    QTest.keyClick(view.buttons[19], Qt.Key_Return)
    assert picker.color() == QColor('#E2F0D9') and picker._flyout is None
    assert selected[-1] == QColor('#E2F0D9')
    QApplication.processEvents()
    picker.showPalette()
    view = picker._flyout.view
    oldChanged = len(changed)
    QTest.mouseClick(view.buttons[19], Qt.LeftButton)
    assert len(changed) == oldChanged and selected[-1] == picker.color()
    QApplication.processEvents()
    picker.showPalette()
    QTest.mouseClick(picker._flyout.view.automaticButton, Qt.LeftButton)
    assert picker.isAutomatic() and picker.color() == QColor('black') and selected[-1] == QColor('black')
    QApplication.processEvents()
    picker.showPalette()
    picker.setAutomaticColor('#112233')
    assert picker._flyout.view.automaticButton.color == QColor('#112233')
    picker.setColor('#7030A0')
    assert picker._flyout.view.buttons[-1].selected and not picker.isAutomatic()
    QTest.keyClick(picker._flyout.view.buttons[-1], Qt.Key_Escape)
    assert picker._flyout is None and picker.color() == QColor('#7030A0')
    QApplication.processEvents()

    # Popup hiding (the native outside-click path) releases its tracked reference.
    picker.showPalette()
    popup = picker._flyout
    popup.hide()
    assert picker._flyout is None
    QApplication.processEvents()
    if QApplication.platformName() == 'windows':
        picker.showPalette()
        QTest.qWait(210)
        QTest.mouseClick(owner.windowHandle(), Qt.LeftButton, pos=QPoint(20, 20))
        QApplication.processEvents()
        assert picker._flyout is None and picker.color() == QColor('#7030A0')
    picker.showPalette()
    picker.setEnabled(False)
    assert picker._flyout is None
    picker.showPalette()
    assert picker._flyout is None
    picker.setEnabled(True)
    picker.showPalette()
    picker.hide()
    assert picker._flyout is None
    picker.show()
    QApplication.processEvents()

    # More Colors opens the actual existing ColorDialog, without stacking popups.
    picker.setAlphaEnabled(True)
    picker.showPalette()
    QTest.mouseClick(picker._flyout.view.moreButton, Qt.LeftButton)
    assert picker._flyout is None and isinstance(picker._dialog, ColorDialog)
    dialog = picker._dialog
    assert dialog.parentWidget() is owner and dialog.enableAlpha
    picker.showColorDialog()
    picker.showPalette()
    assert picker._dialog is dialog and picker._flyout is None
    QTest.qWait(230)
    oldColor = picker.color()
    dialog.setColor(QColor('#80ABCDEF'))
    assert picker.color() == oldColor  # edits are a draft
    QTest.mouseClick(dialog.cancelButton, Qt.LeftButton)
    QTest.qWait(150)
    assert picker._dialog is None and picker.color() == oldColor
    picker.showColorDialog()
    dialog = picker._dialog
    QTest.qWait(230)
    dialog.setColor(QColor('#80ABCDEF'))
    QTest.mouseClick(dialog.yesButton, Qt.LeftButton)
    QTest.qWait(150)
    assert picker._dialog is None and picker.color() == QColor('#80ABCDEF'), (picker._dialog, picker.color().name(QColor.HexArgb))
    assert selected[-1] == QColor('#80ABCDEF') and not picker.isAutomatic()
    picker.showColorDialog()
    QTest.qWait(230)
    oldChanged, oldSelected = len(changed), len(selected)
    QTest.mouseClick(picker._dialog.yesButton, Qt.LeftButton)
    QTest.qWait(150)
    assert len(changed) == oldChanged and len(selected) == oldSelected + 1
    assert themeColor() == accent

    # Button QSS remains identical; transparent custom colors have a checkerboard.
    reference = DropDownPushButton(owner)
    reference.resize(picker.size())
    reference.show()
    picker.setColor('#0078D4')
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        for scale in (1, 2):
            actual, expected = render(picker, scale), render(reference, scale)
            assert picker.styleSheet().strip() == reference.styleSheet().strip()
            assert actual.pixelColor(15 * scale, 16 * scale) == QColor('#0078D4')
            for x, y in ((0, 16), (29, 16), (20, 0), (20, 31)):
                assert actual.pixelColor(x * scale, y * scale) == expected.pixelColor(x * scale, y * scale)
    picker.setColor(QColor(255, 0, 0, 0))
    assert render(picker).pixelColor(7, 8) != render(picker).pixelColor(11, 8)
    demo = ColorPickerDemo()
    demo.resize(900, 800)
    demo.show()
    QApplication.processEvents()
    assert isinstance(demo.dropDownPalette, DropDownColorPalette)
    assert demo.dropDownPalette.size() == QSize(54, 32)
    demo.dropDownPalette.setColor('#ABCDEF')
    assert '#abcdef' in demo.dropDownColorLabel.text()
    demo.close()
    owner.close()
    QApplication.processEvents()
    print('PASS: 70 exact colors, 1x/2x rendering, QSS, independent colors, keyboard/mouse, '
          'popup lifecycle, real ColorDialog draft/accept/cancel/alpha, lightweight gallery')
    print('Preview:', previewPath)


if __name__ == '__main__':
    run()
