"""Exercise the owned Qt color editor; never read pixels from the user's desktop."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import DropDownColorPicker, DropDownPushButton, Theme, setTheme, themeColor
from qfluentwidgets_pro.components.widgets.drop_down_color_picker import _ColorPickerView
from gallery_fixtures.color_picker_demo import ColorPickerDemo


def render(widget, scale=1):
    QApplication.processEvents()
    image = QImage(round(widget.width() * scale), round(widget.height() * scale), QImage.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(scale)
    image.fill(Qt.transparent)
    widget.render(image, QPoint(), renderFlags=QWidget.DrawChildren)
    return image


def typeText(edit, text):
    edit.setFocus()
    edit.selectAll()
    QTest.keyClicks(edit, text)


def run():
    app = QApplication([])
    setTheme(Theme.LIGHT)
    accent = QColor(themeColor())
    view = _ColorPickerView('#FF29F1FF')
    view.show()
    QTest.qWait(20)
    assert view.size() == QSize(320, 608)
    assert view.huePanel.size() == QSize(288, 288)
    assert view.hexEdit.text() == '#ff29f1ff'
    assert [edit.text() for edit in view.edits] == ['41', '241', '255', '255']
    assert view.brightnessSlider.value() == 255
    assert view.buttonBar.geometry().bottom() < view.height()
    draft = []
    view.previewed.connect(lambda color: draft.append(QColor(color)))
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        for scale in (1, 2):
            raster = render(view.huePanel, scale)
            assert raster.pixelColor(0, 0).alpha() == 0
            # The square is hue across X, saturation down Y, independent of V.
            actual = raster.pixelColor(100 * scale, 2 * scale)
            expected = QColor.fromHsvF(100 / 287, 1 - 2 / 287, 1)
            assert max(abs(a - b) for a, b in zip(actual.getRgb()[:3], expected.getRgb()[:3])) <= 5
            assert min(raster.pixelColor(100 * scale, 285 * scale).getRgb()[:3]) >= 250
        assert view.color() == QColor('#FF29F1FF')
    setTheme(Theme.LIGHT)
    view.setColor('#80112233')
    typeText(view.edits[0], '255')
    assert view.color() == QColor('#80FF2233') and view.sliders[0].value() == 255
    assert view.hexEdit.text() == '#80ff2233' and view.edits[0].text() == '255'
    view.sliders[1].setValue(120)
    assert view.color().green() == 120 and view.edits[1].text() == '120'
    view.sliders[3].setValue(31)
    assert view.color().alpha() == 31 and view.hexEdit.text().startswith('#1f')
    typeText(view.hexEdit, '#abcdef')
    assert view.color() == QColor('#1FABCDEF')
    typeText(view.hexEdit, '#40234567')
    assert view.color() == QColor('#40234567')
    assert [edit.text() for edit in view.edits] == ['35', '69', '103', '64']
    old = view.color()
    typeText(view.hexEdit, '#12')
    assert view.color() == old
    accepted = []
    view.confirmed.connect(lambda color: accepted.append(QColor(color)))
    view.confirm()
    assert not accepted and view.hexEdit.isError()
    view._restoreHex()
    assert view.hexEdit.text() == '#40234567' and not view.hexEdit.isError()
    # Alpha's zero end renders checkerboard, while its handle stays opaque.
    alpha = view.sliders[3]
    assert alpha.checkerboard and alpha.stops[0].alpha() == 0 and alpha.stops[-1].alpha() == 255

    # Model switching does not convert/round-trip the draft unnecessarily.
    old = view.color()
    view.modeComboBox.setCurrentIndex(1)
    assert view.color() == old and ''.join(label.text() for label in view.labels) == 'HSVA'
    assert [slider.maximum() for slider in view.sliders] == [359, 100, 100, 255]
    view.sliders[0].setValue(210)
    view.sliders[1].setValue(100)
    view.sliders[2].setValue(100)
    assert abs(view.color().hsvHue() - 210) <= 1 and view.color().alpha() == 64
    view.sliders[1].setValue(0)
    assert view.color().red() == view.color().green() == view.color().blue()
    assert view.sliders[0].value() == 210
    view.sliders[1].setValue(100)
    assert abs(view.color().hsvHue() - 210) <= 1
    view.sliders[2].setValue(0)
    view.sliders[0].setValue(35)
    assert view.color().value() == 0 and view.sliders[0].value() == 35
    view.sliders[2].setValue(100)
    assert abs(view.color().hsvHue() - 35) <= 1
    view.modeComboBox.setCurrentIndex(0)
    assert [slider.maximum() for slider in view.sliders] == [255] * 4
    # Brightness changes do not lose hue/saturation at black in RGB mode either.
    view.setColor('#800078D4')
    view.brightnessSlider.setValue(0)
    assert view.color().value() == 0 and view.color().alpha() == 128
    view.brightnessSlider.setValue(255)
    assert abs(view.color().hsvHue() - QColor('#0078D4').hsvHue()) <= 1
    before = view.color()
    QTest.mouseClick(view.huePanel, Qt.RightButton, pos=QPoint(40, 50))
    assert view.color() == before
    QTest.mouseClick(view.huePanel, Qt.LeftButton, pos=QPoint(130, 100))
    assert abs(view._hue - 130 / 287) < .001 and abs(view._saturation - (1 - 100 / 287)) < .001
    assert view.color().alpha() == 128
    QTest.keyClick(view.huePanel, Qt.Key_Right)
    assert abs(view._hue - 131 / 287) < .001
    assert draft
    view.close()

    owner = QWidget()
    owner.resize(900, 900)
    picker = DropDownColorPicker('#0078D4', owner)
    picker.resize(picker.sizeHint())
    picker.move(420, 20)
    owner.show()
    owner.activateWindow()
    QTest.qWait(30)
    assert picker.size() == QSize(54, 32) and isinstance(picker, DropDownPushButton)
    assert picker.isAlphaEnabled() and picker.color() == QColor('#0078D4')
    copy = picker.color()
    copy.setRed(255)
    assert picker.color() == QColor('#0078D4')
    for invalid in (QColor(), 'not a color', object()):
        try:
            picker.setColor(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid color accepted')
        assert picker.color() == QColor('#0078D4')
    changed, selected, previews, canceled = [], [], [], []
    picker.colorChanged.connect(lambda color: changed.append(QColor(color)))
    picker.colorSelected.connect(lambda color: selected.append(QColor(color)))
    picker.colorPreviewed.connect(lambda color: previews.append(QColor(color)))
    picker.pickingCanceled.connect(lambda: canceled.append(True))
    QTest.mouseClick(picker, Qt.RightButton)
    assert picker._flyout is None
    QTest.mouseClick(picker, Qt.LeftButton)
    QTest.qWait(210)
    assert picker._flyout and picker._flyout.isVisible()
    view = picker._flyout.view
    view.sliders[0].setValue(123)
    assert picker.color() == QColor('#0078D4') and previews and not changed
    QTest.mouseClick(view.cancelButton, Qt.LeftButton)
    assert picker._flyout is None and picker.color() == QColor('#0078D4') and canceled == [True]
    QApplication.processEvents()
    picker.showPicker()
    view = picker._flyout.view
    typeText(view.hexEdit, '#80abcdef')
    QTest.mouseClick(view.yesButton, Qt.LeftButton)
    assert picker._flyout is None and picker.color() == QColor('#80ABCDEF')
    assert changed == selected == [QColor('#80ABCDEF')] and len(canceled) == 1
    QApplication.processEvents()
    picker.showPicker()
    QTest.mouseClick(picker._flyout.view.yesButton, Qt.LeftButton)
    assert len(changed) == 1 and len(selected) == 2
    QApplication.processEvents()
    picker.showPicker()
    picker.setColor('#112233')
    assert picker._flyout.view.color() == QColor('#112233')
    QTest.keyClick(picker._flyout.view.hexEdit, Qt.Key_Escape)
    assert picker._flyout is None and picker.color() == QColor('#112233')
    QApplication.processEvents()

    # Native nested dropdown: choosing HSV must not dismiss the outer editor.
    picker.showPicker()
    QTest.qWait(210)
    view = picker._flyout.view
    QTest.mouseClick(view.modeComboBox, Qt.LeftButton)
    QTest.qWait(210)
    assert picker._flyout is not None and view.modeComboBox.dropMenu is not None
    menu = view.modeComboBox.dropMenu
    rect = menu.view.visualItemRect(menu.view.item(1))
    QTest.mouseClick(menu.view.viewport(), Qt.LeftButton, pos=rect.center())
    QApplication.processEvents()
    assert picker._flyout is not None and view.modeComboBox.currentText() == 'HSV'
    assert picker.color() == QColor('#112233')
    picker.closePicker()
    QApplication.processEvents()

    # Smaller screen: the editor scrolls but confirm/cancel remain within its border.
    class SmallScreen:
        def availableGeometry(self):
            return QRect(0, 0, 900, 400)
    with patch.object(picker, 'screen', return_value=SmallScreen()):
        picker.showPicker()
        QApplication.processEvents()
        view = picker._flyout.view
        assert view.height() == 364
        assert view.buttonBar.geometry().bottom() < view.height()
        assert view.scrollArea.verticalScrollBar().maximum() > 0
        view.scrollArea.verticalScrollBar().setValue(view.scrollArea.verticalScrollBar().maximum())
        assert view.edits[3].isVisible()
    picker.closePicker()
    QApplication.processEvents()
    picker.setColor('#80ABCDEF')
    picker.showPicker()
    picker.setAlphaEnabled(False)
    assert picker._flyout is None and not picker.isAlphaEnabled() and picker.color().alpha() == 255
    picker.showPicker()
    assert not picker._flyout.view.edits[3].isVisible()
    assert picker._flyout.view.hexEdit.text() == '#abcdef'
    picker.closePicker()
    QApplication.processEvents()
    picker.showPicker()
    picker.setEnabled(False)
    assert picker._flyout is None
    picker.showPicker()
    assert picker._flyout is None
    picker.setEnabled(True)
    picker.showPicker()
    picker.hide()
    assert picker._flyout is None
    picker.show()
    QApplication.processEvents()
    if QApplication.platformName() == 'windows':
        picker.showPicker()
        QTest.qWait(210)
        QTest.mouseClick(owner.windowHandle(), Qt.LeftButton, pos=QPoint(20, 20))
        QApplication.processEvents()
        assert picker._flyout is None

    # Render a full-height owned editor at the reference's 125% size, both themes.
    paths = []
    picker.setAlphaEnabled(True)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        preview = _ColorPickerView('#0078D4' if theme == Theme.LIGHT else '#29F1FF')
        preview.show()
        QApplication.processEvents()
        preview.hexEdit.clearFocus()
        image = render(preview, 1.25)
        path = str(Path(tempfile.gettempdir()) / ('codex-drop-down-color-picker-%s.png' % theme.value))
        assert image.save(path)
        paths.append(path)
        preview.close()
    setTheme(Theme.LIGHT)
    assert themeColor() == accent
    demo = ColorPickerDemo()
    demo.show()
    QApplication.processEvents()
    assert demo.dropDownPicker.size() == QSize(54, 32)
    demo.alphaCheckBox.setChecked(False)
    assert not demo.dropDownPicker.isAlphaEnabled()
    demo.dropDownPicker.setColor('#ABCDEF')
    assert '#ffabcdef' in demo.dropDownPickerLabel.text()
    demo.close()
    owner.close()
    QApplication.processEvents()
    print('PASS: gradients, RGBA/HSV/hex synchronization, gray/black hue retention, alpha, '
          'draft/accept/cancel, nested popup, small screens, 1x/2x, independent colors and gallery')
    print('Previews:', paths)


if __name__ == '__main__':
    run()
