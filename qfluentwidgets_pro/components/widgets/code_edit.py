"""Native code editor with versioned, asynchronous Pygments highlighting."""
from bisect import bisect_right
from enum import Enum
import re

from PySide6.QtCore import QEvent, QObject, QRect, QRunnable, QThreadPool, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFontDatabase, QPainter, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from ...common.config import qconfig
from ...common.style_sheet import isDarkTheme
from .line_edit import PlainTextEdit


class CodeLanguage(Enum):
    PYTHON = 'python'
    C = 'c'
    CPP = 'cpp'
    CSHARP = 'csharp'
    JAVA = 'java'
    JAVASCRIPT = 'javascript'
    TYPESCRIPT = 'typescript'
    JSON = 'json'
    HTML = 'html'
    CSS = 'css'
    XML = 'xml'
    YAML = 'yaml'
    TOML = 'toml'
    INI = 'ini'
    BASH = 'bash'
    POWERSHELL = 'powershell'
    SQL = 'sql'
    GO = 'go'
    RUST = 'rust'
    MARKDOWN = 'markdown'


class _LexSignals(QObject):
    finished = Signal(int, object, str)


class _LexJob(QRunnable):
    def __init__(self, version, text, lexer):
        super().__init__()
        self.version, self.text, self.lexer = version, text, lexer
        self.signals = _LexSignals()

    def run(self):
        try:
            lines = self.text.split('\n')
            starts, offset = [], 0
            maps = {}
            for row, line in enumerate(lines):
                starts.append(offset)
                offset += len(line) + 1
                if any(ord(char) > 0xffff for char in line):
                    positions = [0]
                    for char in line:
                        positions.append(positions[-1] + (2 if ord(char) > 0xffff else 1))
                    maps[row] = positions
            spans = [[] for _ in lines]
            # Full-document lexing preserves nested/embedded languages and
            # multiline state. Never mutate Qt documents from this thread.
            for index, token, value in self.lexer.get_tokens_unprocessed(self.text):
                name = str(token)
                if name.startswith('Token.Text'):
                    continue
                for piece in value.split('\n'):
                    if index >= len(self.text):
                        break
                    row = bisect_right(starts, index) - 1
                    col = index - starts[row]
                    length = min(len(piece), len(lines[row]) - col)
                    if length > 0:
                        mapping = maps.get(row)
                        start = mapping[col] if mapping else col
                        end = mapping[col + length] if mapping else col + length
                        spans[row].append((start, end - start, name))
                    index += len(piece) + 1
            self.signals.finished.emit(self.version, (lines, spans), '')
        except Exception as error:
            self.signals.finished.emit(self.version, None, str(error))


class _CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.lines, self.spans = [], []
        self.formats = {}

    def tokenFormat(self, token):
        if token in self.formats:
            return self.formats[token]
        dark = isDarkTheme()
        if token.startswith('Token.Comment'):
            color = '#80a879' if dark else '#6a9955'
        elif token.startswith(('Token.Name.Tag', 'Token.Name.Attribute')):
            color = '#ff8585' if dark else '#ff3636'
        elif token.startswith('Token.Literal.String'):
            color = '#a4d88b' if dark else '#32a852'
        elif token.startswith('Token.Keyword.Constant'):
            color = '#dc9cff' if dark else '#c000d4'
        elif token.startswith('Token.Keyword'):
            color = '#72b9ff' if dark else '#005cc5'
        elif token.startswith('Token.Literal.Number'):
            color = '#93caff' if dark else '#005cc5'
        elif token.startswith(('Token.Name.Function', 'Token.Name.Class')):
            color = '#e8cc85' if dark else '#795e26'
        elif token.startswith(('Token.Generic.Heading', 'Token.Generic.Subheading')):
            color = '#72b9ff' if dark else '#005cc5'
        else:
            color = '#eeeeee' if dark else '#172b4d'
        result = QTextCharFormat()
        result.setForeground(QColor(color))
        self.formats[token] = result
        return result

    def highlightBlock(self, text):
        row = self.currentBlock().blockNumber()
        if row >= len(self.lines) or self.lines[row] != text:
            return
        for start, length, token in self.spans[row]:
            self.setFormat(start, length, self.tokenFormat(token))


class _LineNumberArea(QWidget):
    def paintEvent(self, event):
        self.parent()._paintLineNumbers(event)


class CodeEdit(PlainTextEdit):
    """Code editor with 20 languages, native undo/IME and a line-number gutter.

    Pygments is required only when constructing CodeEdit, not importing the
    widget library. Plain text APIs are inherited from QPlainTextEdit.
    """
    languageChanged = Signal(str)
    highlightingFinished = Signal()
    highlightingFailed = Signal(str)

    def __init__(self, parent=None, language=CodeLanguage.PYTHON):
        try:
            from pygments.lexers import get_lexer_by_name
        except ImportError as error:
            raise ImportError('CodeEdit requires Pygments: pip install -r requirements-codeedit.txt') from error
        super().__init__(parent)
        self._getLexer = get_lexer_by_name
        self._version = 0
        self._job = None
        self._language = ''
        self._indentSize = 4
        self._lineNumbersVisible = True
        self._highlightLimit = 1_000_000
        self._pendingRows = []
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(11)
        self.setFont(font)
        self.lineNumberArea = _LineNumberArea(self)
        self.highlighter = _CodeHighlighter(self.document())
        self._lexTimer = QTimer(self)
        self._lexTimer.setSingleShot(True)
        self._lexTimer.setInterval(80)
        self._lexTimer.timeout.connect(self._startHighlighting)
        self._applyTimer = QTimer(self)
        self._applyTimer.setSingleShot(True)
        self._applyTimer.timeout.connect(self._applyHighlightBatch)
        self.blockCountChanged.connect(self._updateGutter)
        self.updateRequest.connect(self._updateGutterRegion)
        self.cursorPositionChanged.connect(self._highlightCurrentLine)
        self.document().contentsChange.connect(self._documentChanged)
        qconfig.themeChangedFinished.connect(self._updateTheme)
        self.setIndentSize(4)
        self._updateGutter()
        self._highlightCurrentLine()
        self.setLanguage(language)

    @staticmethod
    def supportedLanguages():
        return tuple(language.value for language in CodeLanguage)

    def language(self):
        return self._language

    def setLanguage(self, language):
        language = language.value if isinstance(language, CodeLanguage) else str(language).lower()
        language = {'py': 'python', 'c++': 'cpp', 'c#': 'csharp', 'js': 'javascript',
                    'ts': 'typescript', 'shell': 'bash', 'ps1': 'powershell',
                    'md': 'markdown', 'yml': 'yaml'}.get(language, language)
        if language not in self.supportedLanguages():
            raise ValueError('Unsupported CodeEdit language: ' + language)
        if language == self._language:
            return
        self._lexer = self._getLexer(language)
        self._language = language
        self._version += 1
        self.highlighter.lines, self.highlighter.spans = [], []
        self.highlighter.rehighlight()
        self._lexTimer.start()
        self.languageChanged.emit(language)

    def setIndentSize(self, size):
        self._indentSize = max(1, min(16, int(size)))
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * self._indentSize)

    def indentSize(self):
        return self._indentSize

    def setLineNumbersVisible(self, visible):
        self._lineNumbersVisible = bool(visible)
        self.lineNumberArea.setVisible(visible)
        self._updateGutter()

    def _gutterWidth(self):
        return (20 + self.fontMetrics().horizontalAdvance('9') *
                len(str(max(1, self.blockCount())))) if self._lineNumbersVisible else 0

    def _updateGutter(self, *_):
        self.setViewportMargins(self._gutterWidth(), 0, 0, 0)
        # The inherited Fluent stylesheet adds left padding. Anchor to the
        # viewport rather than contentsRect(), so the two row fills meet.
        self.lineNumberArea.setGeometry(QRect(self.viewport().x() - self._gutterWidth(), self.viewport().y(),
                                              self._gutterWidth(), self.viewport().height()))
        self.lineNumberArea.update()

    def _updateGutterRegion(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self._gutterWidth(), rect.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'lineNumberArea'):
            self._updateGutter()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.FontChange and hasattr(self, 'lineNumberArea'):
            self.setIndentSize(self._indentSize)
            self._updateGutter()

    def _paintLineNumbers(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.setFont(self.font())
        block = self.firstVisibleBlock()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        current = self.textCursor().blockNumber()
        while block.isValid() and top <= event.rect().bottom():
            height = self.blockBoundingRect(block).height()
            if block.isVisible() and top + height >= event.rect().top():
                line = block.layout().lineAt(0)
                lineTop = top + line.y() if line.isValid() else top
                lineHeight = line.height() if line.isValid() else self.fontMetrics().height()
                if block.blockNumber() == current and not self.isReadOnly():
                    # The final block's bounding rect includes bottom document
                    # margin. Match the text line, not that enlarged rectangle.
                    painter.fillRect(0, round(lineTop), self._gutterWidth(), round(lineHeight),
                                     QColor(255, 255, 255, 18) if isDarkTheme() else QColor(0, 0, 0, 24))
                painter.setPen(QColor('#aaaaaa' if isDarkTheme() else '#646464'))
                painter.drawText(0, round(lineTop), self._gutterWidth() - 8,
                                 round(lineHeight), Qt.AlignRight | Qt.AlignVCenter,
                                 str(block.blockNumber() + 1))
            top += height
            block = block.next()

    def _highlightCurrentLine(self):
        selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(255, 255, 255, 18) if isDarkTheme()
                                           else QColor(0, 0, 0, 24))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)
        self.setExtraSelections(selections)
        self.lineNumberArea.update()

    def setReadOnly(self, readonly):
        super().setReadOnly(readonly)
        if hasattr(self, 'lineNumberArea'):
            self._highlightCurrentLine()

    def _updateTheme(self):
        self.highlighter.formats.clear()
        self.highlighter.rehighlight()
        self._highlightCurrentLine()

    def _documentChanged(self, position, removed, added):
        if not removed and not added:
            return
        self._version += 1
        self._pendingRows.clear()
        self._applyTimer.stop()
        self._lexTimer.start()

    def _startHighlighting(self):
        if self._job is not None:
            return  # Its completion starts the latest revision, never a queued backlog.
        text = self.toPlainText()
        if len(text) > self._highlightLimit:
            self.highlighter.lines, self.highlighter.spans = [], []
            self.highlighter.rehighlight()
            self.highlightingFailed.emit(self.tr('Highlighting skipped: document exceeds 1,000,000 characters'))
            return
        self._job = _LexJob(self._version, text, self._lexer)
        self._job.signals.finished.connect(self._lexFinished, Qt.QueuedConnection)
        QThreadPool.globalInstance().start(self._job)

    @Slot(int, object, str)
    def _lexFinished(self, version, result, error):
        self._job = None
        if version != self._version:
            self._lexTimer.start(0)
            return
        if error:
            self.highlightingFailed.emit(error)
            return
        lines, spans = result
        oldLines, oldSpans = self.highlighter.lines, self.highlighter.spans
        self._pendingRows = [i for i in range(len(lines)) if i >= len(oldLines)
                             or oldLines[i] != lines[i] or oldSpans[i] != spans[i]]
        self.highlighter.lines, self.highlighter.spans = lines, spans
        self._applyVersion = version
        self._applyHighlightBatch()

    def _applyHighlightBatch(self):
        if self._applyVersion != self._version:
            self._pendingRows.clear()
            return
        batch, self._pendingRows = self._pendingRows[:128], self._pendingRows[128:]
        for row in batch:
            block = self.document().findBlockByNumber(row)
            if block.isValid():
                self.highlighter.rehighlightBlock(block)
        if self._pendingRows:
            self._applyTimer.start(0)
        else:
            self.highlightingFinished.emit()

    def _indentSelection(self, backwards):
        cursor = self.textCursor()
        first = self.document().findBlock(cursor.selectionStart()).blockNumber()
        end = cursor.selectionEnd()
        last = self.document().findBlock(end).blockNumber()
        if cursor.hasSelection() and end == self.document().findBlock(end).position():
            last = max(first, last - 1)
        cursor.beginEditBlock()
        for row in range(last, first - 1, -1):
            block = self.document().findBlockByNumber(row)
            edit = QTextCursor(block)
            if backwards:
                text = block.text()
                count = 1 if text.startswith('\t') else min(
                    self._indentSize, len(text) - len(text.lstrip(' ')))
                for _ in range(count):
                    edit.deleteChar()
            else:
                edit.insertText(' ' * self._indentSize)
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if self.isReadOnly():
            return super().keyPressEvent(event)
        key = event.key()
        if key in (Qt.Key_Tab, Qt.Key_Backtab) and not (event.modifiers() & Qt.ControlModifier):
            backwards = key == Qt.Key_Backtab or bool(event.modifiers() & Qt.ShiftModifier)
            if self.textCursor().hasSelection() or backwards:
                self._indentSelection(backwards)
            else:
                column = self.textCursor().positionInBlock()
                self.insertPlainText(' ' * (self._indentSize - column % self._indentSize))
            return
        if key in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() == Qt.NoModifier:
            cursor = self.textCursor()
            prefix = cursor.block().text()[:cursor.positionInBlock()]
            indent = re.match(r'[ \t]*', prefix).group()
            if prefix.rstrip().endswith('{') or (self._language == 'python' and prefix.rstrip().endswith(':')):
                indent += ' ' * self._indentSize
            cursor.beginEditBlock()
            cursor.insertText('\n' + indent)
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            return
        super().keyPressEvent(event)
