"""Audit component strings and exercise Qt's real translation-context fallback.

Run with py -3.9 tests/check_i18n.py. No translation API or optional imports
are needed by the static audit. Runtime tests use an in-memory English catalog.
"""
import ast
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PACKAGE = ROOT / 'qfluentwidgets_pro'
TEMPLATE = PACKAGE / '_rc/i18n/qfluentwidgets.en_US.ts'
SOURCE_DIRS = ('components', 'window', 'common', 'multimedia')


def translation_keys():
    """Collect literal tr()/QCoreApplication.translate() keys without imports."""
    keys = set()

    class Visitor(ast.NodeVisitor):
        context = None

        def visit_ClassDef(self, node):
            previous, self.context = self.context, node.name
            self.generic_visit(node)
            self.context = previous

        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute):
                if (node.func.attr == 'tr' and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == 'self'):
                    assert self.context and node.args
                    assert isinstance(node.args[0], ast.Constant), (
                        path, node.lineno, 'tr() must receive a literal source string')
                    keys.add((self.context, node.args[0].value))
                elif (node.func.attr == 'translate' and isinstance(node.func.value, ast.Name)
                      and node.func.value.id in ('QCoreApplication', 'QApplication')):
                    assert len(node.args) >= 2
                    assert all(isinstance(arg, ast.Constant) for arg in node.args[:2])
                    keys.add(tuple(arg.value for arg in node.args[:2]))
            self.generic_visit(node)

    for directory in SOURCE_DIRS:
        for path in sorted((PACKAGE / directory).rglob('*.py')):
            Visitor().visit(ast.parse(path.read_text(encoding='utf-8-sig')))
    return keys


def catalog_entries():
    entries = {}
    contexts = set()
    for context in ET.parse(TEMPLATE).getroot().findall('context'):
        name = context.findtext('name')
        assert name not in contexts, ('Duplicate context', name)
        contexts.add(name)
        for message in context.findall('message'):
            source = message.findtext('source')
            key = (name, source)
            assert key not in entries, ('Duplicate translation', key)
            translation = message.find('translation')
            assert translation is not None and translation.get('type') is None, key
            assert translation.text == source, ('English template must use source == translation', key)
            assert not re.search(r'[\u4e00-\u9fff]', source), ('Non-English source', key)
            entries[key] = source
    return entries


def check_catalog():
    entries = catalog_entries()
    required = translation_keys()
    missing = required - entries.keys()
    assert not missing, 'Missing English TS entries: ' + repr(sorted(missing))

    # Guard direct user-facing literals. Color models, key names, numerical
    # values and caller-supplied labels are data, not localizable prose.
    ui_setters = {'setText', 'setToolTip', 'setAccessibleName',
                  'setAccessibleDescription', 'setPlaceholderText',
                  'setWindowTitle', 'setStatusTip', 'setLabelText'}
    for directory in SOURCE_DIRS:
        for path in sorted((PACKAGE / directory).rglob('*.py')):
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr in ui_setters and node.args):
                    value = node.args[0]
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        assert not re.search(r'[A-Za-z]{2,}|[\u4e00-\u9fff]', value.value), (
                            path.relative_to(ROOT), node.lineno, 'Missing tr()', value.value)
    return entries, len(required)


def check_runtime(entries):
    from unittest.mock import patch
    from PySide6.QtCore import QDate, QDateTime, QTime, QTranslator
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtWidgets import QApplication, QFileDialog, QWidget
    from qfluentwidgets_pro import (
        AudioWaveformWidget, AvatarPicker, CircleColorPicker, DropAnyWidget,
        DropSingleFileWidget, DropSingleFolderWidget, DropMultiFoldersWidget,
        DropMultiFilesWidget, DropDownColorPalette, DropDownColorPicker,
        GuideWindow, InteractiveRatingWidget, MessageBoxBase, PipsPager,
        RatingWidget, RoundProgressToast, ScreenColorPicker, ShortcutPicker,
        SwitchButton, WaitingDialog,
    )
    from qfluentwidgets_pro.components.date_time import (
        CalendarPicker, FastCalendarPicker, RangeCalendarPicker,
        FastRangeCalendarPicker, CalendarTimePicker, FastCalendarTimePicker,
        DatePicker,
    )
    from qfluentwidgets_pro.components.date_time.date_picker import MonthFormatter
    from qfluentwidgets_pro.components.widgets._shortcut_picker_dialog import _ShortcutPickerDialog
    from qfluentwidgets_pro.components.widgets.drop_down_color_palette import _PaletteView
    from qfluentwidgets_pro.components.widgets.drop_down_color_picker import _ColorPickerView
    from qfluentwidgets_pro.components.widgets.screen_color_picker import _PickerOverlay

    class CatalogTranslator(QTranslator):
        def isEmpty(self):
            return False

        def translate(self, context, source, disambiguation=None, n=-1):
            # None, rather than the source string, allows PySide's inheritance
            # fallback to reach the class/mixin that actually defines tr().
            if (context, source) in entries:
                return translated(context, source)
            return None

    def translated(context, source):
        return '[' + context + '] ' + source

    app = QApplication.instance() or QApplication([])
    owner = QWidget()
    widgets = []
    # Without a translator, built-in defaults must be English. Explicit empty
    # content and business strings are preserved, not replaced or translated.
    toast = RoundProgressToast(parent=owner)
    assert toast.content == 'Loading, please wait'
    toast.close()
    assert RoundProgressToast('', parent=owner).content == ''
    assert RoundProgressToast('Caller content', parent=owner).content == 'Caller content'

    translator = CatalogTranslator()
    assert app.installTranslator(translator)
    try:
        for cls in (CalendarPicker, FastCalendarPicker):
            picker = cls(owner)
            assert picker.text() == translated('CalendarPicker', 'Pick a date')
            picker.reset()
            assert picker.text() == translated('CalendarPicker', 'Pick a date')
            widgets.append(picker)
        for cls in (RangeCalendarPicker, FastRangeCalendarPicker):
            picker = cls(owner)
            expected = translated('_RangePickerMixin', 'Pick a date range')
            assert picker.text() == expected
            picker.setDateRange(QDate(2026, 10, 1), QDate(2026, 10, 6))
            assert picker.text() == '2026-10-01 - 2026-10-06'
            picker.reset()
            assert picker.text() == expected
            widgets.append(picker)
        for cls in (CalendarTimePicker, FastCalendarTimePicker):
            picker = cls(owner)
            expected = translated('_CalendarTimePickerMixin', 'Pick a date and time')
            assert picker.text() == expected
            picker.setDateTime(QDateTime(QDate(2026, 10, 6), QTime(12, 30)))
            assert picker.text() == '2026-10-06 12:30:00'
            picker.reset()
            assert picker.text() == expected
            widgets.append(picker)
        assert MonthFormatter().encode(1) == translated('MonthFormatter', 'January')
        assert DatePicker(owner).YEAR == translated('DatePicker', 'year')

        circle = CircleColorPicker([], owner)
        assert circle.accessibleName() == translated('CircleColorPicker', 'Color palette')
        assert circle.accessibleDescription() == translated('CircleColorPicker', 'No color selected')
        for cls in (RatingWidget, InteractiveRatingWidget):
            assert cls(parent=owner).accessibleName() == translated('RatingWidget', 'Rating')
        toast = RoundProgressToast(parent=owner)
        assert toast.content == translated('RoundProgressToast', 'Loading, please wait')
        toast.setContent('Caller content')
        assert toast.content == 'Caller content'
        toast.close()
        assert WaitingDialog(parent=owner).title() == translated('WaitingDialog', 'Please wait...')
        assert WaitingDialog('Caller title', 'Caller content', owner).title() == 'Caller title'
        for cls in (DropMultiFilesWidget, DropSingleFileWidget, DropSingleFolderWidget,
                    DropMultiFoldersWidget, DropAnyWidget):
            drop = cls(parent=owner)
            assert drop.orLabel.text() == translated('DropMultiFilesWidget', 'or')
            drop.setFileExtensions('*.wav')
            assert drop.fileExtensions() == translated('DropMultiFilesWidget', 'Files') + ' (*.wav)'
            drop.setFileExtensions('*.wav', 'Caller filter')
            assert drop.fileExtensions() == 'Caller filter (*.wav)'
            drop.setFileExtensions('')
            context = cls.__name__ if (cls.__name__, 'All files (*.*)') in entries else 'DropMultiFilesWidget'
            assert drop.fileExtensions() == translated(context, 'All files (*.*)')
            drop.setLabelText('Caller label')
            assert drop.label.text() == 'Caller label'
        avatar = AvatarPicker(parent=owner)
        with patch.object(QFileDialog, 'getOpenFileName', return_value=('', '')) as choose:
            avatar.chooseImage()
        assert choose.call_args.args[3] == translated('AvatarPicker', 'Images (*.png *.jpg *.jpeg *.bmp *.webp)')

        picker = ShortcutPicker(parent=owner)
        assert picker.dialogTitle() == translated('ShortcutPicker', 'Activate shortcut')
        dialog = _ShortcutPickerDialog(picker, owner)
        assert dialog.yesButton.text() == translated('_ShortcutPickerDialog', 'Save')
        assert dialog.resetButton.text() == translated('_ShortcutPickerDialog', 'Reset')
        assert dialog.cancelButton.text() == translated('_ShortcutPickerDialog', 'Cancel')
        assert MessageBoxBase(owner).yesButton.text() == translated('MessageBoxBase', 'OK')
        assert SwitchButton(owner).text == translated('SwitchButton', 'Off')
        assert PipsPager(parent=owner).preButton.toolTip() == translated('PipsPager', 'Previous Page')

        palette = DropDownColorPalette(parent=owner)
        paletteView = _PaletteView(palette)
        assert paletteView.moreButton.text() == translated('_PaletteView', 'More Colors...')
        assert DropDownColorPicker(parent=owner).accessibleName() == translated('DropDownColorPicker', 'Color picker')
        colorView = _ColorPickerView(QColor('red'), parent=owner)
        assert colorView.edits[0].accessibleName() == translated('_ColorPickerView', '%1 value').replace('%1', 'R')
        colorView.modeComboBox.setCurrentIndex(1)
        assert colorView.sliders[0].accessibleName() == translated('_ColorPickerView', '%1 slider').replace('%1', 'H')
        screen = ScreenColorPicker(parent=owner)
        overlay = _PickerOverlay(screen, None, owner.rect(), QImage())
        assert overlay.accessibleName() == translated('_PickerOverlay', 'Screen color picking: click to select, Escape to cancel')
        overlay.close()
        waveform = AudioWaveformWidget(parent=owner)
        waveform.setSamples([0.] * 1234, 1000)
        assert waveform.accessibleDescription() == translated('AudioWaveformWidget', 'Duration: %1 ms').replace('%1', '1234')

        guide = GuideWindow()
        guide.addPage(QWidget())
        assert guide.previousButton.text() == translated('GuideWindow', 'Previous')
        assert guide.nextButton.text() == translated('GuideWindow', 'Finish')
        guide.close()
        guide.deleteLater()
    finally:
        app.removeTranslator(translator)
        owner.close()
        owner.deleteLater()
        app.processEvents()


if __name__ == '__main__':
    entries, required = check_catalog()
    check_runtime(entries)
    print('PASS: %d literal translation keys covered; English defaults, inherited/Fast '
          'contexts, dialogs, accessibility, file filters and caller text verified' % required)
