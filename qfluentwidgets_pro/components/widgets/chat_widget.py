"""QQ-style native chat surface; networking and model clients belong to callers.

Import this module explicitly. Rich code/formula support can reach Pygments and
Matplotlib; it is intentionally not re-exported by the lightweight package root.
"""

from dataclasses import dataclass
from uuid import uuid4

from PySide6.QtCore import QEvent, QRectF, QSize, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QFontMetrics, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QSizePolicy,
    QSplitter, QSplitterHandle, QVBoxLayout, QWidget,
)

from ...common.config import qconfig
from ...common.font import getFont, setFont
from ...common.icon import FluentIcon, FluentIconBase, getIconColor
from ...common.style_sheet import isDarkTheme, themeColor
from ..layout.flow_layout import FlowLayout
from .button import PrimaryPushButton, PushButton, RoundToolButton, TransparentToolButton
from .chat_content import _CodeBlock, _MarkdownBlock, splitMessage
from .label import AvatarWidget, BodyLabel
from .scroll_area import ScrollArea


class _JumpButton(RoundToolButton):
    """Keep the standard translucent button above an opaque circular backing."""

    def _drawBackground(self, painter, rect, r, isDark):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#202020' if isDark else '#ffffff'))
        painter.drawEllipse(rect)
        super()._drawBackground(painter, rect, r, isDark)


class _ChatDivider(QSplitterHandle):
    """A one-pixel line with a forgiving hit area; Qt handles native dragging."""

    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setCursor(Qt.SplitVCursor)
        self._hovered = False
        self._pressed = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        dark = isDarkTheme()
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#202020' if dark else '#ffffff'))
        color = themeColor() if self._hovered or self._pressed else QColor('#383838' if dark else '#e5e5e5')
        painter.setPen(QPen(color, 1))
        y = self.height() // 2
        painter.drawLine(0, y, self.width() - 1, y)


class _ChatSplitter(QSplitter):
    """Native resize mechanics, without the component library's splitter style."""

    def createHandle(self):
        return _ChatDivider(self.orientation(), self)


@dataclass(frozen=True)
class ChatMessage:
    """A snapshot: ids are stable, content stays the exact caller-supplied text."""
    id: str
    role: str
    content: str
    name: str = ''
    streaming: bool = False
    kind: str = 'text'


@dataclass(frozen=True)
class _MessageAction:
    id: str
    icon: object
    toolTip: str
    callback: object = None
    roles: object = None
    kinds: object = None

    def accepts(self, message):
        return ((self.roles is None or message.role in self.roles)
                and (self.kinds is None or message.kind in self.kinds))


class _ThumbIcon(FluentIconBase):
    """Small native outline thumbs, without adding fonts or SVG dependencies."""
    def __init__(self, down=False):
        self.down = down

    def path(self, theme=None):
        return ''

    def icon(self, theme=None, color=None):
        return self.qicon()

    def render(self, painter, rect, theme=None, **attributes):
        painter.save()
        painter.translate(rect.x(), rect.y())
        painter.scale(rect.width() / 16, rect.height() / 16)
        if self.down:
            painter.translate(0, 16)
            painter.scale(1, -1)
        pen = QPen(QColor(getIconColor() if theme is None else getIconColor(theme)), 1.2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(1, 7, 3, 8), .7, .7)
        path = QPainterPath()
        path.moveTo(4, 7)
        path.lineTo(7.5, 3)
        path.cubicTo(7.5, .5, 10.5, .5, 10.5, 3)
        path.lineTo(10, 6.5)
        path.lineTo(13.5, 6.5)
        path.quadTo(15.5, 6.5, 15, 8.5)
        path.lineTo(13.7, 13.8)
        path.quadTo(13.4, 15, 12, 15)
        path.lineTo(4, 15)
        path.closeSubpath()
        painter.drawPath(path)
        painter.restore()


class _MessageToolBar(QWidget):
    def __init__(self, row):
        super().__init__(row.body)
        self.row = row
        self.buttons = {}
        self.flowLayout = FlowLayout(self)
        self.flowLayout.setContentsMargins(0, 0, 0, 0)
        self.flowLayout.setHorizontalSpacing(4)
        self.flowLayout.setVerticalSpacing(4)
        self.syncActions()

    def syncActions(self):
        # Configuration changes rebuild buttons. Text chunks/theme changes do
        # not: host-owned enabled/checkable states survive streaming updates.
        for button in self.buttons.values():
            self.flowLayout.removeWidget(button)
            button.hide()
            button.deleteLater()
        self.buttons.clear()
        for action in self.row.chat._messageActions.values():
            if not action.accepts(self.row.message):
                continue
            button = TransparentToolButton(action.icon, self)
            button.setFixedSize(28, 28)
            button.setIconSize(QSize(16, 16))
            button.setToolTip(action.toolTip)
            button.setAccessibleName(action.toolTip)
            button.clicked.connect(
                lambda checked=False, actionId=action.id:
                self.row.chat._triggerMessageAction(self.row.message.id, actionId))
            self.buttons[action.id] = button
            self.flowLayout.addWidget(button)
        self.updateVisibility()

    def updateVisibility(self):
        self.setVisible(self.row.chat._messageToolBarEnabled and bool(self.buttons))

    def naturalWidth(self):
        return max(0, len(self.buttons) * 32 - 4)

    def fitWidth(self, width):
        self.setFixedWidth(max(28, min(width, self.naturalWidth() + 1)))
        # Leave a pixel of room for FlowLayout's inclusive right-edge test.
        self.setFixedHeight(self.flowLayout.heightForWidth(self.width()) or 28)


class _ChatInput(QPlainTextEdit):
    submitted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sendOnEnter = True
        self._preediting = False
        self.setFrameShape(QFrame.NoFrame)
        setFont(self, 14)

    def inputMethodEvent(self, event):
        self._preediting = bool(event.preeditString())
        super().inputMethodEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not self._preediting:
            modifiers = event.modifiers()
            submit = (modifiers == Qt.NoModifier if self.sendOnEnter
                      else modifiers == Qt.ControlModifier)
            if submit:
                self.submitted.emit()
                event.accept()
                return
        super().keyPressEvent(event)


class _Bubble(QWidget):
    def __init__(self, chat, outgoing, parent=None):
        super().__init__(parent)
        self.chat, self.outgoing = chat, outgoing
        self.blocks = []
        self.contentLayout = QVBoxLayout(self)
        self.contentLayout.setContentsMargins(14, 10, 14, 10)
        self.contentLayout.setSpacing(10)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = self.chat._bubbleColor(self.outgoing)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(self.rect()), 12, 12)

    def setContent(self, text, force=False):
        parsed = splitMessage(text)
        for index, (kind, language, content) in enumerate(parsed):
            key = (kind, language)
            if index < len(self.blocks) and self.blocks[index][0] != key:
                self._removeFrom(index)
            if index == len(self.blocks):
                block = _CodeBlock(language, self) if kind == 'code' else _MarkdownBlock(self)
                self.blocks.append((key, block))
                self.contentLayout.addWidget(block)
                block.warning.connect(self.chat.renderWarning)
                if isinstance(block, _MarkdownBlock):
                    block.anchorClicked.connect(self.chat.linkClicked)
            block = self.blocks[index][1]
            if isinstance(block, _MarkdownBlock):
                block.setContent(content, self.chat._mathEnabled, self.chat._formulaRenderer, force)
            else:
                block.setContent(content, force)
        self._removeFrom(len(parsed))
        self.update()

    def _removeFrom(self, index):
        for _, block in self.blocks[index:]:
            self.contentLayout.removeWidget(block)
            block.hide()
            block.deleteLater()
        del self.blocks[index:]


class _MessageRow(QWidget):
    def __init__(self, chat, message, avatar, image=None, widget=None):
        super().__init__(chat.messageContainer)
        self.chat, self.message = chat, message
        self.outgoing = message.role == 'user'
        self.image = QImage(image) if image is not None else None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.avatar = AvatarWidget(self)
        self.avatar.setRadius(18)
        if avatar is not None:
            self.avatar.setImage(avatar)
        self.avatar.setText(message.name or ('U' if self.outgoing else 'A'))
        self.body = QWidget(self)
        body = QVBoxLayout(self.body)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(6)
        self.nameLabel = QLabel(message.name, self.body)
        self.nameLabel.setWordWrap(True)
        self.nameLabel.setVisible(bool(message.name))
        body.addWidget(self.nameLabel)
        self.bubble = _Bubble(chat, self.outgoing, self.body)
        alignment = Qt.AlignRight if self.outgoing else Qt.AlignLeft
        body.addWidget(self.bubble, 0, alignment)
        if self.image is not None:
            self.imageLabel = QLabel(self.bubble)
            self.imageLabel.setAlignment(Qt.AlignCenter)
            self.imageLabel.setCursor(Qt.PointingHandCursor)
            self.imageLabel.installEventFilter(self)
            self.bubble.contentLayout.addWidget(self.imageLabel)
        elif widget is not None:
            self.bubble.contentLayout.addWidget(widget)
        self.statusLabel = QLabel(self.body)
        body.addWidget(self.statusLabel)
        self.statusLabel.setVisible(message.streaming)
        self.messageToolBar = _MessageToolBar(self)
        body.addWidget(self.messageToolBar, 0, alignment)
        if self.outgoing:
            layout.addStretch()
            layout.addWidget(self.body, 0, Qt.AlignTop)
            layout.addWidget(self.avatar, 0, Qt.AlignTop)
        else:
            layout.addWidget(self.avatar, 0, Qt.AlignTop)
            layout.addWidget(self.body, 0, Qt.AlignTop)
            layout.addStretch()
        self.nameLabel.setAlignment(Qt.AlignRight if self.outgoing else Qt.AlignLeft)
        self.applyTheme()

    def eventFilter(self, watched, event):
        if (getattr(self, 'imageLabel', None) is watched and event.type() == QEvent.MouseButtonRelease
                and event.button() == Qt.LeftButton):
            self.chat.imageClicked.emit(self.message.id)
        return super().eventFilter(watched, event)

    def applyTheme(self):
        muted = '#999999' if isDarkTheme() else '#707070'
        for label in (self.nameLabel, self.statusLabel):
            label.setStyleSheet('QLabel { color: %s; background: transparent; }' % muted)
        self.statusLabel.setText(self.chat.tr('Typing...'))
        if self.message.kind == 'text':
            self.bubble.setContent(self.message.content, force=True)
        self.bubble.update()

    def setMessage(self, message):
        self.message = message
        self.bubble.setContent(message.content)
        self.statusLabel.setVisible(message.streaming)

    def fitWidth(self, available):
        maximum = max(60, min(self.chat._maximumBubbleWidth, int(available * .76), available - 58))
        if self.image is not None:
            size = self.image.size()
            size.scale(max(1, min(maximum - 28, size.width())), min(260, size.height()), Qt.KeepAspectRatio)
            self.imageLabel.setPixmap(QPixmap.fromImage(self.image).scaled(
                size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            width = min(maximum, size.width() + 28)
        elif self.message.kind == 'widget':
            width = maximum
        else:
            text = self.message.content
            hasRichBlocks = any(key[0] == 'code' for key, _ in self.bubble.blocks) or '\n' in text
            natural = QFontMetrics(getFont(14)).horizontalAdvance(text) + 36
            width = maximum if hasRichBlocks else min(maximum, max(60, natural))
            # A long sender name must not force a one-word message to overflow.
        self.bubble.setFixedWidth(width)
        toolWidth = (self.messageToolBar.naturalWidth() if self.chat._messageToolBarEnabled else 0)
        bodyWidth = max(width, min(maximum, toolWidth + 1))
        self.body.setFixedWidth(bodyWidth)
        self.messageToolBar.fitWidth(bodyWidth)


class ChatWidget(QWidget):
    """Native chat history, customizable toolbars and a composer.

    ``role='user'`` is right-aligned; assistant/system messages are left-aligned.
    sendRequested only emits draft text; the application owns adding messages,
    network requests, persistence and cancellation. All mutation APIs run on the
    GUI thread. Worker signals can connect to appendText via queued connections.
    """
    sendRequested = Signal(str)
    stopRequested = Signal()
    messageAdded = Signal(str)
    messageChanged = Signal(str)
    messageRemoved = Signal(str)
    linkClicked = Signal(QUrl)
    imageClicked = Signal(str)
    renderWarning = Signal(str)
    messageActionTriggered = Signal(str, str)  # actionId, messageId

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = {}
        self._dirty = set()
        self._mathEnabled = True
        self._formulaRenderer = None
        self._maximumBubbleWidth = 680
        self._following = True
        self._busy = False
        self._bubbleColors = None
        self._messageToolBarEnabled = False
        self._messageActions = {
            action.id: action for action in (
                _MessageAction('copy', FluentIcon.COPY, self.tr('Copy message'), kinds=('text', 'image')),
                _MessageAction('retry', FluentIcon.SYNC, self.tr('Retry'), roles=('assistant',), kinds=('text',)),
                _MessageAction('like', _ThumbIcon(), self.tr('Like'), roles=('assistant',), kinds=('text',)),
                _MessageAction('dislike', _ThumbIcon(True), self.tr('Dislike'), roles=('assistant',), kinds=('text',)),
                _MessageAction('readAloud', FluentIcon.VOLUME, self.tr('Read aloud'), roles=('assistant',), kinds=('text',)),
                _MessageAction('share', FluentIcon.SHARE, self.tr('Share')),
            )
        }
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._flush)
        setFont(self, 14)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.splitter = _ChatSplitter(Qt.Vertical, self)
        self.splitter.setHandleWidth(6)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setOpaqueResize(True)
        self._composerSizes = None
        layout.addWidget(self.splitter)
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setMinimumHeight(100)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messageContainer = QWidget()
        self.messageLayout = QVBoxLayout(self.messageContainer)
        self.messageLayout.setContentsMargins(24, 24, 24, 24)
        self.messageLayout.setSpacing(24)
        self.messageLayout.addStretch()
        self.scrollArea.setWidget(self.messageContainer)
        self.scrollArea.viewport().installEventFilter(self)
        self.splitter.addWidget(self.scrollArea)
        bar = self.scrollArea.verticalScrollBar()
        bar.valueChanged.connect(self._scrollChanged)
        bar.rangeChanged.connect(self._rangeChanged)
        self.jumpButton = _JumpButton(FluentIcon.DOWN, self.scrollArea.viewport())
        self.jumpButton.setFixedSize(36, 36)
        self.jumpButton.setIconSize(QSize(18, 18))
        self.jumpButton.setToolTip(self.tr('Jump to latest'))
        self.jumpButton.setAccessibleName(self.tr('Jump to latest'))
        self.jumpButton.clicked.connect(self.scrollToBottom)
        self.jumpButton.hide()
        self.composer = QWidget(self)
        self.composer.setObjectName('chatComposer')
        composer = QVBoxLayout(self.composer)
        composer.setContentsMargins(20, 12, 20, 14)
        composer.setSpacing(6)
        self.toolBar = QWidget(self.composer)
        tools = QHBoxLayout(self.toolBar)
        tools.setContentsMargins(0, 0, 0, 0)
        tools.setSpacing(0)
        self.leftToolBar = QWidget(self.toolBar)
        self.rightToolBar = QWidget(self.toolBar)
        self.leftToolLayout = QHBoxLayout(self.leftToolBar)
        self.rightToolLayout = QHBoxLayout(self.rightToolBar)
        for side in (self.leftToolLayout, self.rightToolLayout):
            side.setContentsMargins(0, 0, 0, 0)
            side.setSpacing(6)
        tools.addWidget(self.leftToolBar)
        tools.addStretch()
        tools.addWidget(self.rightToolBar)
        composer.addWidget(self.toolBar)
        self.inputEdit = _ChatInput(self.composer)
        self.inputEdit.setMinimumHeight(76)
        self.inputEdit.setPlaceholderText(self.tr('Write a message...'))
        self.inputEdit.setAccessibleName(self.tr('Message input'))
        self.inputEdit.submitted.connect(self.send)
        self.inputEdit.textChanged.connect(self._updateSendButton)
        composer.addWidget(self.inputEdit, 1)
        bottom = QHBoxLayout()
        self.shortcutLabel = QLabel(self.composer)
        bottom.addWidget(self.shortcutLabel)
        bottom.addStretch()
        self.stopButton = PushButton(self.tr('Stop'), self.composer)
        self.stopButton.clicked.connect(self.stopRequested)
        self.stopButton.hide()
        bottom.addWidget(self.stopButton)
        self.sendButton = PrimaryPushButton(self.tr('Send'), self.composer)
        self.sendButton.setMinimumWidth(90)
        self.sendButton.clicked.connect(self.send)
        bottom.addWidget(self.sendButton)
        composer.addLayout(bottom)
        self.splitter.addWidget(self.composer)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([460, 184])
        self.setSendOnEnter(True)
        self._updateSendButton()
        qconfig.themeChangedFinished.connect(self._applyTheme)
        self._applyTheme()

    def sizeHint(self):
        return QSize(800, 650)

    def addToolButton(self, icon, toolTip='', callback=None, side='left'):
        """Add a Fluent tool button; caller-provided labels are not translated."""
        button = TransparentToolButton(icon, self.toolBar)
        button.setFixedSize(32, 32)
        button.setToolTip(toolTip)
        button.setAccessibleName(toolTip)
        if callback is not None:
            button.clicked.connect(callback)
        self.addToolWidget(button, side)
        return button

    def addToolWidget(self, widget, side='left'):
        """Either toolbar also accepts custom QWidget controls or menus."""
        if side not in ('left', 'right'):
            raise ValueError("Toolbar side must be 'left' or 'right'")
        (self.leftToolLayout if side == 'left' else self.rightToolLayout).addWidget(widget)

    def removeToolWidget(self, widget):
        for layout in (self.leftToolLayout, self.rightToolLayout):
            layout.removeWidget(widget)
        widget.hide()
        widget.setParent(None)

    def setMessageToolBarEnabled(self, enabled=True):
        """Show/hide action bars below all existing and future messages.

        Disabled by default. Copy is local; other built-in actions only emit
        messageActionTriggered(actionId, messageId), never call an AI/backend.
        """
        self._messageToolBarEnabled = bool(enabled)
        for row in self._rows.values():
            row.messageToolBar.updateVisibility()
        self._fitRows()

    def isMessageToolBarEnabled(self):
        return self._messageToolBarEnabled

    def addMessageAction(self, actionId, icon, toolTip='', callback=None, roles=None, kinds=None):
        """Add a button to applicable message bars; callback receives messageId.

        roles/kinds default to all. Caller-provided labels are never translated.
        Configure actions once; existing and future rows both use the definition.
        """
        if not isinstance(actionId, str) or not actionId or actionId in self._messageActions:
            raise ValueError('Message action id is empty, invalid or duplicated')
        if callback is not None and not callable(callback):
            raise TypeError('Message action callback must be callable or None')
        def validate(values, allowed):
            if values is None:
                return None
            values = (values,) if isinstance(values, str) else tuple(values)
            if not values or not set(values).issubset(allowed):
                raise ValueError('Invalid message action filter')
            return values
        roles = validate(roles, ('user', 'assistant', 'system'))
        kinds = validate(kinds, ('text', 'image', 'widget'))
        self._messageActions[actionId] = _MessageAction(actionId, icon, str(toolTip), callback, roles, kinds)
        self._syncMessageActions()

    def removeMessageAction(self, actionId):
        del self._messageActions[actionId]
        self._syncMessageActions()

    def clearMessageActions(self):
        """Remove definitions; custom input-area toolbars are not affected."""
        self._messageActions.clear()
        self._syncMessageActions()

    def messageToolBar(self, messageId):
        return self._rows[messageId].messageToolBar

    def messageActionButton(self, messageId, actionId):
        """Return the row's button, or None when a filter excludes the action."""
        return self.messageToolBar(messageId).buttons.get(actionId)

    def _syncMessageActions(self):
        for row in self._rows.values():
            row.messageToolBar.syncActions()
        self._fitRows()

    def _triggerMessageAction(self, messageId, actionId):
        row, action = self._rows.get(messageId), self._messageActions.get(actionId)
        # Guard delayed clicks when an action/message has just been removed.
        if row is None or action is None or not action.accepts(row.message):
            return
        if action.callback is not None:
            action.callback(messageId)
        elif actionId == 'copy':
            if row.image is not None:
                QApplication.clipboard().setImage(row.image)
            else:
                QApplication.clipboard().setText(row.message.content)
        self.messageActionTriggered.emit(actionId, messageId)

    def addMessage(self, content='', role='assistant', name='', avatar=None, messageId=None, streaming=False):
        """Add text/Markdown and return its id. No automatic backend request."""
        return self._add(content, role, name, avatar, messageId, streaming)

    def addImageMessage(self, image, role='assistant', name='', avatar=None, messageId=None):
        """Explicit local image/QImage/QPixmap; remote URLs are never fetched."""
        if isinstance(image, QPixmap):
            image = image.toImage()
        elif not isinstance(image, QImage):
            image = QImage(str(image))
        if image.isNull():
            raise ValueError('Cannot load chat image')
        return self._add('', role, name, avatar, messageId, False, 'image', image=image)

    def addWidgetMessage(self, widget, role='assistant', name='', avatar=None, messageId=None):
        """Embed an application-provided card (file, voice, task, etc.)."""
        if not isinstance(widget, QWidget):
            raise TypeError('A widget message requires a QWidget')
        return self._add('', role, name, avatar, messageId, False, 'widget', widget=widget)

    def _add(self, content, role, name, avatar, messageId, streaming, kind='text', **kwargs):
        if role not in ('user', 'assistant', 'system'):
            raise ValueError("Message role must be 'user', 'assistant' or 'system'")
        messageId = str(messageId) if messageId is not None else uuid4().hex
        if not messageId or messageId in self._rows:
            raise ValueError('Message id is empty or duplicated')
        message = ChatMessage(messageId, role, str(content), str(name), bool(streaming), kind)
        row = _MessageRow(self, message, avatar, **kwargs)
        self._rows[messageId] = row
        self.messageLayout.insertWidget(self.messageLayout.count() - 1, row)
        self._fitRows()
        self.messageAdded.emit(messageId)
        return messageId

    def message(self, messageId):
        return self._rows[messageId].message

    def messages(self):
        return [row.message for row in self._rows.values()]

    @Slot(str, str)
    def appendText(self, messageId, delta):
        """Coalesce stream chunks at 40 ms; unchanged blocks are reused."""
        row = self._rows[messageId]
        self.setMessageText(messageId, row.message.content + delta)

    @Slot(str, str)
    def setMessageText(self, messageId, content):
        from dataclasses import replace
        row = self._rows[messageId]
        if row.message.kind != 'text':
            raise ValueError('Only text messages support content updates')
        row.message = replace(row.message, content=str(content))
        self._dirty.add(messageId)
        if not self._timer.isActive():
            self._timer.start()
        self.messageChanged.emit(messageId)

    def setMessageStreaming(self, messageId, streaming):
        from dataclasses import replace
        row = self._rows[messageId]
        row.message = replace(row.message, streaming=bool(streaming))
        self._dirty.add(messageId)
        self._flush()
        self.messageChanged.emit(messageId)

    def finishMessage(self, messageId):
        self.setMessageStreaming(messageId, False)

    def removeMessage(self, messageId):
        row = self._rows.pop(messageId)
        self._dirty.discard(messageId)
        self.messageLayout.removeWidget(row)
        row.hide()
        row.deleteLater()
        self.messageRemoved.emit(messageId)

    def clear(self):
        """Clear history only; draft text and custom tools are retained."""
        self._timer.stop()
        self._dirty.clear()
        for messageId in list(self._rows):
            self.removeMessage(messageId)
        self._following = True
        self.jumpButton.hide()

    def setMathEnabled(self, enabled):
        self._mathEnabled = bool(enabled)
        self._refreshContent()

    def setFormulaRenderer(self, renderer):
        """Optional callable(expression, color, pointSize) -> QImage."""
        if renderer is not None and not callable(renderer):
            raise TypeError('Formula renderer must be callable or None')
        self._formulaRenderer = renderer
        self._refreshContent()

    def setMaximumBubbleWidth(self, width):
        if int(width) < 100:
            raise ValueError('Maximum bubble width must be at least 100')
        self._maximumBubbleWidth = int(width)
        self._fitRows()

    def setBubbleColors(self, incomingLight, incomingDark, outgoingLight, outgoingDark):
        colors = [QColor(c) for c in (incomingLight, incomingDark, outgoingLight, outgoingDark)]
        if not all(c.isValid() for c in colors):
            raise ValueError('Invalid bubble color')
        self._bubbleColors = colors
        self._refreshContent()

    def setComposerVisible(self, visible):
        """Hide the input area and divider, retaining the previous height split."""
        visible = bool(visible)
        if visible == (not self.composer.isHidden()):
            return
        if not visible:
            self._composerSizes = self.splitter.sizes()
        self.composer.setVisible(visible)
        if visible and self._composerSizes is not None:
            self.splitter.setSizes(self._composerSizes)

    def setSendOnEnter(self, enabled):
        self.inputEdit.sendOnEnter = bool(enabled)
        self.shortcutLabel.setText(self.tr('Enter to send, Shift+Enter for a new line') if enabled
                                  else self.tr('Ctrl+Enter to send, Enter for a new line'))

    def setBusy(self, busy):
        """Show Stop while streaming; stopRequested never stops a backend itself."""
        self._busy = bool(busy)
        self.stopButton.setVisible(self._busy)
        self._updateSendButton()

    @Slot()
    def send(self):
        content = self.inputEdit.toPlainText()
        if not content.strip() or self._busy:
            return
        self.inputEdit.clear()
        self.sendRequested.emit(content)

    def _updateSendButton(self):
        self.sendButton.setEnabled(bool(self.inputEdit.toPlainText().strip()) and not self._busy)

    def _bubbleColor(self, outgoing):
        if self._bubbleColors is not None:
            return self._bubbleColors[(2 if outgoing else 0) + int(isDarkTheme())]
        return QColor(('#253c53' if outgoing else '#333333') if isDarkTheme()
                      else ('#e6f2ff' if outgoing else '#f1f1f1'))

    def _applyTheme(self):
        dark = isDarkTheme()
        background, foreground, muted = ('#202020', '#eeeeee', '#999999') if dark else ('#ffffff', '#202020', '#707070')
        self.scrollArea.setStyleSheet('QScrollArea { background: %s; border: none; }' % background)
        self.messageContainer.setStyleSheet('QWidget { background: transparent; }')
        self.scrollArea.viewport().setStyleSheet('background: %s;' % background)
        self.composer.setStyleSheet('QWidget#chatComposer { background: %s; }' % background)
        self.splitter.handle(1).update()
        self.jumpButton.update()
        self.inputEdit.setStyleSheet('QPlainTextEdit { border: none; padding: 4px 0; background: transparent; color: %s; }' % foreground)
        self.shortcutLabel.setStyleSheet('QLabel { color: %s; background: transparent; }' % muted)
        self._refreshContent()

    def _refreshContent(self):
        for row in self._rows.values():
            row.applyTheme()
        self._fitRows()

    def _flush(self):
        self._timer.stop()
        dirty, self._dirty = self._dirty, set()
        for messageId in dirty:
            if messageId in self._rows:
                row = self._rows[messageId]
                row.setMessage(row.message)
        self._fitRows()

    def _fitRows(self):
        width = max(100, self.scrollArea.viewport().width() - 48)
        for row in self._rows.values():
            row.fitWidth(width)
        self.messageLayout.activate()
        if self._following:
            QTimer.singleShot(0, self._followBottom)

    def _followBottom(self):
        if self._following:
            bar = self.scrollArea.verticalScrollBar()
            bar.setValue(bar.maximum())

    @Slot()
    def scrollToBottom(self):
        self._following = True
        self._followBottom()
        self.jumpButton.hide()

    def _scrollChanged(self, value):
        bar = self.scrollArea.verticalScrollBar()
        self._following = bar.maximum() - value <= 32
        self.jumpButton.setVisible(not self._following)

    def _rangeChanged(self, *_):
        if self._following:
            self._followBottom()

    def eventFilter(self, watched, event):
        if watched is self.scrollArea.viewport() and event.type() == QEvent.Resize:
            self._fitRows()
            self.jumpButton.adjustSize()
            self.jumpButton.move(max(0, watched.width() - self.jumpButton.width() - 18),
                                 max(0, watched.height() - self.jumpButton.height() - 14))
            self.jumpButton.raise_()
        return super().eventFilter(watched, event)
