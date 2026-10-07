"""Owned Qt widgets only: API, capture isolation, lifecycle and high-DPI rendering."""

import os
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QLocale, QPoint, Qt
from PySide6.QtGui import QColor, QImage, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from qfluentwidgets_pro import CardWidget, FluentTranslator, ShortcutPicker, Theme, setTheme, setThemeColor, themeColor
from qfluentwidgets_pro.components.widgets.shortcut_picker import _tokens


def send(target, key, modifiers=Qt.NoModifier, release=False, repeat=False):
    event = QKeyEvent(QEvent.KeyRelease if release else QEvent.KeyPress,
                      key, modifiers, '', repeat)
    QApplication.sendEvent(target, event)


def run():
    app = QApplication([])
    window = QWidget()
    window.resize(900, 600)
    layout = QVBoxLayout(window)
    picker = ShortcutPicker(parent=window)
    layout.addWidget(picker, 0, Qt.AlignLeft)
    layout.addStretch()
    window.show()
    window.activateWindow()
    QTest.qWait(60)
    changed, selected, finished, canceled = [], [], [], []
    picker.keySequenceChanged.connect(lambda seq: changed.append(seq.toString()))
    picker.keySequenceSelected.connect(lambda seq: selected.append(seq.toString()))
    picker.editingFinished.connect(lambda: finished.append(True))
    picker.editingCanceled.connect(lambda: canceled.append(True))
    assert _tokens(picker.keySequence()) == ['Ctrl', 'Shift', 'A']
    assert isinstance(picker, CardWidget) and picker.isClickEnabled()
    assert picker.borderRadius == 8 and picker.cursor().shape() == Qt.PointingHandCursor
    assert picker.keyCaps.testAttribute(Qt.WA_TransparentForMouseEvents)
    assert picker.editButton.testAttribute(Qt.WA_TransparentForMouseEvents)
    assert picker.focusPolicy() == Qt.StrongFocus and picker.editButton.focusPolicy() == Qt.NoFocus
    assert picker.height() == 60
    if app.platformName() == 'windows':
        assert 190 <= picker.sizeHint().width() <= 225
    for value, tokens in [('Ctrl++', ['Ctrl', '+']), ('Ctrl+,', ['Ctrl', ',']),
                          ('Meta', ['Meta']), ('Ctrl+Shift', ['Ctrl', 'Shift']),
                          ('Alt+F8', ['Alt', 'F8'])]:
        picker.setKeySequence(value)
        assert _tokens(picker.keySequence()) == tokens
    before, emissions = picker.keySequence(), len(changed)
    for value in ('garbage', 'Ctrl+K, Ctrl+C', object()):
        try:
            picker.setKeySequence(value)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError('invalid sequence accepted: ' + repr(value))
        assert picker.keySequence() == before and len(changed) == emissions
    copy = picker.keySequence()
    copy.swap(QKeySequence('F1'))
    assert picker.keySequence() == before
    picker.setKeySequence(before)
    assert len(changed) == emissions
    picker.clear()
    assert picker.keySequence().isEmpty()
    picker.reset()
    assert picker.keySequence() == QKeySequence('Ctrl+Shift+A')
    picker.setDefaultKeySequence('Alt+F9')
    picker.reset()
    assert picker.keySequence() == QKeySequence('Alt+F9')
    picker.setDefaultKeySequence('Ctrl+Shift+A')
    picker.reset()

    hits = []
    registered = QShortcut(QKeySequence('Ctrl+Shift+A'), window)
    registered.setContext(Qt.ApplicationShortcut)
    registered.activated.connect(lambda: hits.append(True))

    def openEditor():
        app.processEvents()
        QTest.mouseClick(window.windowHandle(), Qt.LeftButton,
                         pos=picker.editButton.mapTo(window, picker.editButton.rect().center()))
        QTest.qWait(240)
        dialog = picker._dialog
        assert dialog is not None and dialog.isVisible() and dialog._capturing
        assert dialog.widget.size().width() == 560 and dialog.widget.height() == 400
        picker.showEditor()
        assert picker._dialog is dialog
        return dialog

    def closeEditor(button):
        QTest.mouseClick(button, Qt.LeftButton)
        QTest.qWait(170)
        assert not picker.isEditing()

    cardClicks = []
    picker.clicked.connect(lambda: cardClicks.append(True))
    cap = picker.keyCaps.row.itemAt(0).widget()
    points = [QPoint(6, 6),  # blank padding
              cap.mapTo(picker, cap.rect().center()),  # a key cap
              picker.keyCaps.mapTo(picker, QPoint(cap.width() + 3, 18)),  # gap between caps
              picker.editButton.mapTo(picker, picker.editButton.rect().center())]
    for point in points:
        count = len(cardClicks)
        QTest.mouseClick(window.windowHandle(), Qt.LeftButton, pos=picker.mapTo(window, point))
        QTest.qWait(240)
        assert picker.isEditing() and len(cardClicks) == count + 1
        closeEditor(picker._dialog.cancelButton)
    QTest.mouseClick(picker, Qt.RightButton)
    QTest.mouseRelease(picker, Qt.LeftButton)  # no matching press
    assert not picker.isEditing()
    QTest.mousePress(picker, Qt.LeftButton, pos=QPoint(6, 6))
    assert picker.isPressed
    QTest.mouseRelease(picker, Qt.LeftButton, pos=QPoint(picker.width() + 10, 6))
    assert not picker.isPressed and not picker.isEditing()
    picker.setClickEnabled(False)
    QTest.mouseClick(picker, Qt.LeftButton)
    QTest.keyClick(picker, Qt.Key_Return)
    assert not picker.isEditing()
    picker.setClickEnabled(True)
    for key in (Qt.Key_Return, Qt.Key_Space):
        picker.setFocus()
        QTest.keyClick(picker, key)
        QTest.qWait(240)
        assert picker.isEditing()
        closeEditor(picker._dialog.cancelButton)
    picker.setEnabled(False)
    QTest.mouseClick(picker, Qt.LeftButton)
    assert not picker.isEditing()
    picker.setEnabled(True)

    QTest.mouseMove(picker, QPoint(6, 6))
    QTest.qWait(170)
    assert picker.isHover
    assert picker.backgroundColor.rgba() == picker._hoverBackgroundColor().rgba()
    QTest.mouseMove(window, QPoint(window.width() - 15, window.height() - 15))
    QTest.qWait(170)
    assert not picker.isHover
    assert picker.backgroundColor.rgba() == picker._normalBackgroundColor().rgba()

    dialog = openEditor()
    # Even keys delivered to the footer must be captured, not click Save.
    QTest.keyClick(dialog.yesButton, Qt.Key_A, Qt.ControlModifier | Qt.ShiftModifier)
    assert dialog.sequence == QKeySequence('Ctrl+Shift+A') and not hits
    QTest.keyClick(dialog, Qt.Key_F8, Qt.AltModifier)
    assert dialog.sequence == QKeySequence('Alt+F8')
    assert picker.keySequence() == QKeySequence('Ctrl+Shift+A')
    closeEditor(dialog.cancelButton)
    assert picker.keySequence() == QKeySequence('Ctrl+Shift+A') and canceled
    dialog = openEditor()
    QTest.keyClick(dialog, Qt.Key_F8, Qt.AltModifier)
    closeEditor(dialog.yesButton)
    assert picker.keySequence() == QKeySequence('Alt+F8')
    assert selected[-1] == 'Alt+F8' and finished
    dialog = openEditor()
    QTest.keyClick(dialog, Qt.Key_F2)
    QTest.mouseClick(dialog.resetButton, Qt.LeftButton)
    assert dialog.sequence == QKeySequence('Ctrl+Shift+A')
    assert picker.keySequence() == QKeySequence('Alt+F8')
    closeEditor(dialog.cancelButton)
    assert picker.keySequence() == QKeySequence('Alt+F8')
    dialog = openEditor()
    QTest.mouseClick(dialog.resetButton, Qt.LeftButton)
    closeEditor(dialog.yesButton)
    assert picker.keySequence() == QKeySequence('Ctrl+Shift+A')
    emissions = len(changed)
    dialog = openEditor()
    closeEditor(dialog.yesButton)
    assert len(changed) == emissions and len(selected) == 3

    dialog = openEditor()
    send(dialog, Qt.Key_Meta)
    send(dialog, Qt.Key_Meta, release=True)
    assert _tokens(dialog.sequence) == ['Meta'] and dialog.yesButton.isEnabled()
    send(dialog, Qt.Key_F3, repeat=True)
    assert _tokens(dialog.sequence) == ['Meta']
    send(dialog, Qt.Key_A)
    send(dialog, Qt.Key_Control, Qt.ControlModifier)
    assert _tokens(dialog.sequence) == ['Ctrl', 'A']  # reverse order
    send(dialog, Qt.Key_Control, release=True)
    send(dialog, Qt.Key_A, release=True)
    assert _tokens(dialog.sequence) == ['Ctrl', 'A']  # stable on release
    QTest.keyClick(dialog, Qt.Key_B)
    assert _tokens(dialog.sequence) == ['B']  # no sticky modifier
    QTest.keyClick(dialog.yesButton, Qt.Key_Return)
    assert dialog.sequence == QKeySequence('Return') and picker.isEditing()
    QTest.keyClick(dialog, Qt.Key_Tab)
    assert dialog.sequence == QKeySequence('Tab')
    send(dialog, Qt.Key_Backtab)
    assert dialog.sequence == QKeySequence('Shift+Tab')
    send(dialog, Qt.Key_Backtab, release=True)
    QTest.keyClick(dialog, Qt.Key_Escape)
    QTest.qWait(170)
    assert not picker.isEditing() and picker.keySequence() == QKeySequence('Ctrl+Shift+A')

    picker.setEscapeCancelsCapture(False)
    dialog = openEditor()
    QTest.keyClick(dialog, Qt.Key_Escape)
    assert dialog.sequence == QKeySequence('Esc')
    closeEditor(dialog.yesButton)
    assert picker.keySequence() == QKeySequence('Esc')
    dialog = openEditor()
    send(dialog, Qt.Key_5, Qt.KeypadModifier)
    assert _tokens(dialog.sequence) == ['Num', '5']
    closeEditor(dialog.yesButton)

    # The capture filter is removed before the asynchronous fade-out.
    dialog = openEditor()
    QTest.keyClick(dialog, Qt.Key_F10)
    dialog.accept()
    assert not dialog._capturing
    send(dialog, Qt.Key_F12)
    QTest.qWait(170)
    assert picker.keySequence() == QKeySequence('F10')
    picker.reset()
    window.activateWindow()
    picker.setFocus()
    QTest.qWait(100)
    QTest.keyClick(picker.editButton, Qt.Key_A, Qt.ControlModifier | Qt.ShiftModifier)
    assert hits, 'ApplicationShortcut should work again after closing the editor'

    dialog = openEditor()
    window.resize(1000, 650)
    app.processEvents()
    assert dialog.size() == window.size()
    picker.setEnabled(False)
    QTest.qWait(170)
    assert not picker.isEditing()
    picker.setEnabled(True)
    dialog = openEditor()
    picker.hide()
    QTest.qWait(170)
    assert not picker.isEditing()
    picker.show()

    # A picker may be deleted while its separately parented dialog is active.
    temporary = ShortcutPicker(parent=window)
    layout.insertWidget(0, temporary)
    temporary.show()
    app.processEvents()
    temporary.showEditor()
    QTest.qWait(240)
    doomedDialog = temporary._dialog
    temporary.deleteLater()
    QTest.qWait(180)
    from shiboken6 import isValid
    assert not isValid(temporary)
    if isValid(doomedDialog):
        assert not doomedDialog._capturing
        QTest.qWait(150)  # Deferred deletion can begin the inherited fade-out late.
        assert not doomedDialog.isVisible() and not doomedDialog._capturing
        doomedDialog.deleteLater()
    app.processEvents()

    from gallery_fixtures.shortcut_picker_demo import ShortcutPickerDemo
    demo = ShortcutPickerDemo(window)
    demo.picker.setKeySequence('Alt+F6')
    assert demo.shortcut.key() == QKeySequence('Alt+F6')
    assert 'Alt+F6' in demo.sequenceLabel.text()
    demo.captureEscape.setChecked(True)
    assert not demo.picker.isEscapeCancelsCapture()
    demo.clearButton.click()
    assert demo.shortcut.key().isEmpty()
    demo.deleteLater()

    for locale, title, save, reset in (
            ('zh_CN', '激活快捷键', '保存', '重置'),
            ('zh_TW', '啟用快捷鍵', '儲存', '重設'),
            ('zh_HK', '啟用快捷鍵', '儲存', '重設')):
        translator = FluentTranslator(QLocale(locale))
        app.installTranslator(translator)
        localized = ShortcutPicker(parent=window)
        assert localized.dialogTitle() == title
        localized.show()
        localized.showEditor()
        QTest.qWait(240)
        translatedDialog = localized._dialog
        assert translatedDialog.yesButton.text() == save
        assert translatedDialog.resetButton.text() == reset
        assert translatedDialog.cancelButton.text() == '取消'
        localized.cancelEditing()
        QTest.qWait(170)
        localized.deleteLater()
        app.removeTranslator(translator)

    # Native rendering uses only this owned window; no desktop screen grabs.
    picker.reset()
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        setThemeColor('#19BCD3')
        picker.resize(picker.sizeHint())
        app.processEvents()
        cap = picker.keyCaps.row.itemAt(0).widget()
        for scale in (1, 2):
            raster = QImage(round(cap.width() * scale), round(cap.height() * scale),
                            QImage.Format_ARGB32_Premultiplied)
            raster.setDevicePixelRatio(scale)
            raster.fill(Qt.transparent)
            cap.render(raster, QPoint())
            color = raster.pixelColor(round(8 * scale), round(8 * scale))
            assert color.rgba() == themeColor().rgba(), (color.name(), themeColor().name())
    if os.environ.get('SHORTCUT_PREVIEW_DIR'):
        translator = FluentTranslator(QLocale('zh_CN'))
        app.installTranslator(translator)
        previewDir = Path(os.environ['SHORTCUT_PREVIEW_DIR'])
        previewDir.mkdir(parents=True, exist_ok=True)
        picker.setDialogTitle('激活快捷键')
        picker.setDialogDescription('按下组合键以更改此快捷键')
        setThemeColor('#20DEF0')
        for theme in (Theme.DARK, Theme.LIGHT):
            setTheme(theme)
            picker.resize(picker.sizeHint())
            app.processEvents()
            picker.grab().save(str(previewDir / ('shortcut-' + theme.value.lower() + '.png')))
        setTheme(Theme.DARK)
        dialog = openEditor()
        send(dialog, Qt.Key_Meta)
        QTest.qWait(50)
        dialog.widget.grab().save(str(previewDir / 'shortcut-dialog.png'))
        closeEditor(dialog.cancelButton)
    window.close()
    app.processEvents()
    print('PASS: ShortcutPicker API, transactional editor, Meta/Tab/Enter/Escape, shortcut isolation, cleanup and theme/DPI')


if __name__ == '__main__':
    run()
