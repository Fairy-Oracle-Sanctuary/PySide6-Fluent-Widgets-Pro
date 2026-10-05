"""Run with py -3.9 tests/check_code_edit.py (requires Pygments)."""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from gallery.view.code_edit_demo import SAMPLES
from qfluentwidgets_pro import Theme, setTheme
from qfluentwidgets_pro.components.widgets.code_edit import CodeEdit, CodeLanguage


def wait_highlight(editor):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        QTest.qWait(10)
        if (editor._job is None and not editor._lexTimer.isActive()
                and not editor._applyTimer.isActive()
                and editor.highlighter.lines == editor.toPlainText().split('\n')):
            return
    raise AssertionError('highlight timeout or stale text')


def run():
    app = QApplication([])
    editor = CodeEdit(language=CodeLanguage.JSON)
    editor.resize(800, 500)
    editor.show()
    failures = []
    editor.highlightingFailed.connect(failures.append)
    assert len(editor.supportedLanguages()) == 20
    for language, sample in SAMPLES.items():
        editor.setLanguage(language)
        editor.setPlainText(sample)
        wait_highlight(editor)
        assert any(editor.highlighter.spans), language
    editor.setLanguage('cpp')
    editor.setPlainText('/* start\ninside\nend */\nint value = 2;')
    wait_highlight(editor)
    assert any('Comment' in span[2] for span in editor.highlighter.spans[1])
    # Change a multiline delimiter: downstream lines must be lexed again.
    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(2, QTextCursor.KeepAnchor)
    cursor.insertText('//')
    wait_highlight(editor)
    assert not any('Comment' in span[2] for span in editor.highlighter.spans[1])
    editor.setLanguage('json')
    editor.setPlainText('{"emoji": "🌍", "value": true}')
    wait_highlight(editor)
    spans = editor.highlighter.spans[0]
    boolean = next(span for span in spans if 'Keyword.Constant' in span[2])
    key = next(span for span in spans if 'Name.Tag' in span[2])
    text = editor.toPlainText()
    assert boolean[0] == len(text[:text.index('true')].encode('utf-16-le')) // 2
    before = editor.toPlainText()
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        QTest.qWait(30)
        assert editor.toPlainText() == before
        assert editor.document().firstBlock().layout().formats()
        assert editor.highlighter.tokenFormat(key[2]).foreground().color().name() == (
            '#ff3636' if theme == Theme.LIGHT else '#ff8585')
    editor.setLanguage('python')
    editor.setPlainText('if ready:')
    editor.moveCursor(QTextCursor.End)
    QTest.keyClick(editor, Qt.Key_Return)
    assert editor.toPlainText() == 'if ready:\n    '
    editor.undo()
    assert editor.toPlainText() == 'if ready:'
    editor.setPlainText('one\ntwo\nthree')
    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(8, QTextCursor.KeepAnchor)  # third line isn't selected
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key_Tab)
    assert editor.toPlainText() == '    one\n    two\nthree'
    QTest.keyClick(editor, Qt.Key_Backtab)
    assert editor.toPlainText() == 'one\ntwo\nthree'
    editor.setReadOnly(True)
    QTest.keyClick(editor, Qt.Key_Tab)
    assert editor.toPlainText() == 'one\ntwo\nthree'
    editor.setReadOnly(False)
    editor.setLineNumbersVisible(False)
    assert editor.viewportMargins().left() == 0
    editor.setLineNumbersVisible(True)
    assert editor.viewportMargins().left() > 0
    for text in ('first\nlast', 'first\n', ''):
        editor.setPlainText(text)
        editor.moveCursor(QTextCursor.End)
        editor.setFocus()
        QTest.qWait(20)
        gutter = editor.lineNumberArea.geometry()
        assert gutter.right() + 1 == editor.viewport().x()
        block = editor.textCursor().block()
        line = block.layout().lineAt(0)
        top = editor.blockBoundingGeometry(block).translated(editor.contentOffset()).top() + line.y()
        image = editor.grab().toImage()
        scale = image.devicePixelRatio()
        gx, vx = gutter.right() - 2, editor.viewport().x() + 120
        # Below the last text line both sides must have lost the row highlight.
        y = editor.viewport().y() + top + line.height() + 2
        def sample(x, offset):
            return image.pixelColor(round(x * scale), round((y + offset) * scale))
        assert sample(gx, 0) == sample(gx, 5), 'last-row gutter spill'
        assert sample(vx, 0) == sample(vx, 5), 'last-row viewport spill'
    # Rapid edits / language changes while a job is running.
    editor.setPlainText('print("before")\n' * 3000)
    editor._lexTimer.stop()
    editor._startHighlighting()
    editor.setLanguage('json')
    editor.setPlainText('{"latest": true}')
    wait_highlight(editor)
    assert editor.highlighter.lines == ['{"latest": true}']
    editor.setLanguage('python')
    started = time.monotonic()
    editor.setPlainText('value = "hello" # comment\n' * 5000)
    wait_highlight(editor)
    print('5000-line highlight: %.3fs' % (time.monotonic() - started))
    # A local edit should replace only differing format blocks after lexing.
    editor.moveCursor(QTextCursor.Start)
    editor.insertPlainText('# ')
    wait_highlight(editor)
    assert not failures, failures
    editor.close()
    print('PASS: 20 languages, multiline edits, UTF-16, themes, indent/undo, read-only, gutter, stale jobs')


if __name__ == '__main__':
    run()
