"""Native chat content blocks. Untrusted Markdown cannot load external files."""

import math
import re
from uuid import uuid4

from PySide6.QtCore import QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QFont, QFontDatabase, QImage, QTextDocument, QTextImageFormat
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QTextBrowser, QVBoxLayout

from ...common.icon import FluentIcon
from ...common.font import getFont
from ...common.style_sheet import isDarkTheme
from .button import TransparentToolButton


def splitMessage(text):
    """Split fenced code from Markdown, including unfinished streaming fences.

    Recognizes backtick/tilde fences with up to three spaces indentation. A
    closing fence must use the same character and at least the opener's length.
    """
    blocks, prose, code = [], [], []
    fence = language = None
    for line in text.splitlines(keepends=True):
        candidate = re.match(r'^ {0,3}(`{3,}|~{3,})([^\r\n]*)[\r\n]*$', line)
        if fence is None:
            if candidate and (candidate[1][0] != '`' or '`' not in candidate[2]):
                if prose:
                    blocks.append(('text', '', ''.join(prose)))
                    prose = []
                fence = candidate[1]
                language = candidate[2].strip().split(' ', 1)[0].lower()
            else:
                prose.append(line)
        elif (candidate and candidate[1][0] == fence[0]
              and len(candidate[1]) >= len(fence) and not candidate[2].strip()):
            blocks.append(('code', language, ''.join(code).removesuffix('\n').removesuffix('\r')))
            fence, code = None, []
        else:
            code.append(line)
    if fence is not None:
        blocks.append(('code', language, ''.join(code)))
    if prose:
        blocks.append(('text', '', ''.join(prose)))
    return blocks or [('text', '', '')]


# Inline code is deliberately excluded from formula substitution.
_MATH = re.compile(r'(?P<code>`+[^`]*`+)|(?P<display>(?<!\\)\$\$[\s\S]+?(?<!\\)\$\$|\\\[[\s\S]+?\\\])'
                   r'|(?P<inline>\\\([^\n]+?\\\)|(?<![\\$])\$(?!\$)[^\n$]+?(?<!\\)\$(?!\$))')


class _MarkdownBlock(QTextBrowser):
    warning = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = None
        self._renderer = None
        self._mathEnabled = True
        self.setFrameShape(QFrame.NoFrame)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(0)
        self.setFont(getFont(14))
        self.document().documentLayout().documentSizeChanged.connect(self._fitHeight)

    def loadResource(self, resourceType, name):
        # Markdown images, HTML img/file URLs and network resources are not
        # implicit file/network access. Images must be added explicitly by Qt.
        return None

    def setContent(self, text, mathEnabled=True, renderer=None, force=False):
        if not force and (text, mathEnabled, renderer) == (self._text, self._mathEnabled, self._renderer):
            return
        self._text, self._mathEnabled, self._renderer = text, mathEnabled, renderer
        resources = []
        foreground = '#eeeeee' if isDarkTheme() else '#202020'

        def substitute(match):
            if match['code'] or not mathEnabled:
                return match[0]
            token = 'MATH' + uuid4().hex.upper()
            source = match[0]
            expression = source[2:-2] if source.startswith(('$$', '\\(', '\\[')) else source[1:-1]
            try:
                if renderer is None:
                    from ...common.chat_math import renderFormula
                    image = renderFormula(expression, foreground, 12)
                else:
                    image = renderer(expression, foreground, 12)
                if not isinstance(image, QImage) or image.isNull():
                    raise ValueError('Formula renderer must return a non-empty QImage')
                resources.append((token, source, image, bool(match['display'])))
            except Exception as error:
                # Malformed/custom providers must not tear down a conversation.
                # MathText also raises e.g. ZeroDivisionError for zero-height
                # whitespace-only expressions; always retain the source text.
                resources.append((token, source, None, bool(match['display'])))
                self.warning.emit(self.tr('Could not render formula: %1').replace('%1', str(error)))
            return '\n\n' + token + '\n\n' if match['display'] else token

        markdown = _MATH.sub(substitute, text)
        document = self.document()
        document.clear()
        document.setDefaultStyleSheet(
            'p { margin-top: 0px; margin-bottom: 8px; } '
            'a { color: %s; } code { font-family: Consolas, monospace; } '
            'table { border-collapse: collapse; } td, th { padding: 5px; }'
            % ('#79c0ff' if isDarkTheme() else '#0067c0'))
        document.setMarkdown(markdown, QTextDocument.MarkdownDialectGitHub | QTextDocument.MarkdownNoHTML)
        # Qt's HTML/Markdown import can resolve the widget font to one family;
        # retain the library's full CJK-aware fallback list for native layout.
        document.setDefaultFont(getFont(14))
        for token, source, image, display in resources:
            cursor = document.find(token)
            if cursor.isNull():
                continue
            if image is None:
                cursor.insertText(source)
                continue
            name = QUrl('chat-math:/' + token)
            document.addResource(QTextDocument.ImageResource, name, image)
            imageFormat = QTextImageFormat()
            imageFormat.setName(name.toString())
            imageFormat.setWidth(image.width() / image.devicePixelRatio())
            imageFormat.setHeight(image.height() / image.devicePixelRatio())
            cursor.insertImage(imageFormat)
            if display:
                block = cursor.blockFormat()
                block.setAlignment(Qt.AlignCenter)
                cursor.setBlockFormat(block)
        self.setStyleSheet('QTextBrowser { background: transparent; border: none; padding: 0; color: %s; }' % foreground)
        self.setFont(getFont(14))
        document.setDefaultFont(getFont(14))
        self._fitHeight()

    def _fitHeight(self, *_):
        self.document().setTextWidth(max(20, self.viewport().width()))
        height = math.ceil(self.document().size().height()) + 2
        if self.horizontalScrollBar().maximum() > 0:
            height += self.horizontalScrollBar().sizeHint().height()
        self.setFixedHeight(max(self.fontMetrics().height() + 2, height))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fitHeight()

    def wheelEvent(self, event):
        # One vertical scroll owner for the entire conversation.
        if event.angleDelta().y() and not event.modifiers() & Qt.ShiftModifier:
            event.ignore()
        else:
            super().wheelEvent(event)


class _CodeBlock(QFrame):
    warning = Signal(str)

    def __init__(self, language, parent=None):
        super().__init__(parent)
        self.language, self._text = language, None
        self.setObjectName('chatCodeBlock')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)
        layout.setSpacing(6)
        header = QHBoxLayout()
        self.label = QLabel(language or self.tr('Plain text'), self)
        header.addWidget(self.label)
        header.addStretch()
        self.copyButton = TransparentToolButton(FluentIcon.COPY, self)
        self.copyButton.setFixedSize(26, 26)
        self.copyButton.setToolTip(self.tr('Copy code'))
        self.copyButton.setAccessibleName(self.tr('Copy code'))
        self.copyButton.clicked.connect(self._copy)
        header.addWidget(self.copyButton)
        layout.addLayout(header)
        try:
            from .code_edit import CodeEdit
            self.editor = CodeEdit(self, language=language)
            self.editor.setLineNumbersVisible(False)
        except (ImportError, ValueError):
            # Unknown language and installations without Pygments still display
            # every character; highlighting is an optional enhancement.
            self.editor = QPlainTextEdit(self)
            self.editor.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.editor.setReadOnly(True)
        font = QFont()
        font.setFamilies(['Cascadia Mono', 'Consolas', 'DejaVu Sans Mono', 'monospace'])
        font.setPixelSize(14)
        self.editor.setFont(font)
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.editor.document().setDocumentMargin(2)
        layout.addWidget(self.editor)

    def _copy(self):
        QApplication.clipboard().setText(self._text or '')
        self.copyButton.setToolTip(self.tr('Copied'))

    def setContent(self, text, force=False):
        if not force and self._text == text:
            return
        self._text = text
        position = self.editor.horizontalScrollBar().value()
        self.editor.setPlainText(text)
        self.editor.horizontalScrollBar().setValue(position)
        # Long code gets its own scrolling area rather than a gigantic bubble.
        height = self.editor.fontMetrics().lineSpacing() * (text.count('\n') + 1) + 24
        self.editor.setFixedHeight(min(360, max(48, height)))
        dark = isDarkTheme()
        background, border = ('#262626', '#484848') if dark else ('#ffffff', '#dedede')
        self.setStyleSheet('QFrame#chatCodeBlock { background: %s; border: 1px solid %s; border-radius: 8px; }'
                          'QLabel { background: transparent; color: %s; }'
                          % (background, border, '#aaaaaa' if dark else '#666666'))
        self.editor.setStyleSheet('QPlainTextEdit { background: transparent; border: none; padding: 0; color: %s; }'
                                 % ('#eeeeee' if dark else '#202020'))
        self.copyButton.setToolTip(self.tr('Copy code'))
