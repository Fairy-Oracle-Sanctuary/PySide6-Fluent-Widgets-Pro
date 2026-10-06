"""Native chat regression checks. Run with QT_QPA_PLATFORM=offscreen if needed."""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QEnterEvent, QImage, QMouseEvent, QTextDocument
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from qfluentwidgets_pro import FluentIcon, Theme, setTheme
from qfluentwidgets_pro.components.widgets.chat_content import splitMessage, _MarkdownBlock, _CodeBlock
from qfluentwidgets_pro.components.widgets.chat_widget import ChatWidget
from qfluentwidgets_pro.components.widgets.button import RoundToolButton


def pump(app, duration=.12):
    until = time.monotonic() + duration
    while time.monotonic() < until:
        app.processEvents()
        time.sleep(.002)


def dragDivider(chat, delta, app):
    handle = chat.splitter.handle(1)
    start = handle.rect().center()
    target = handle.mapToGlobal(start) + QPoint(0, delta)
    QTest.mousePress(handle, Qt.LeftButton, Qt.NoModifier, start)
    assert handle._pressed
    event = QMouseEvent(QEvent.MouseMove, QPointF(handle.mapFromGlobal(target)),
                        QPointF(target), Qt.NoButton, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(handle, event)
    QTest.mouseRelease(handle, Qt.LeftButton, Qt.NoModifier, handle.mapFromGlobal(target))
    pump(app)
    assert not handle._pressed


def checkJumpBacking(chat, app):
    host = QWidget()
    host.setObjectName('jumpBackingTest')
    host.resize(64, 64)
    button = type(chat.jumpButton)(FluentIcon.DOWN, host)
    button.setFixedSize(36, 36)
    button.move(14, 14)
    host.show()
    for theme in (Theme.DARK, Theme.LIGHT):
        setTheme(theme)
        for state in ('normal', 'hover', 'pressed', 'disabled'):
            button.isHover = state == 'hover'
            button.isPressed = state == 'pressed'
            button.setEnabled(state != 'disabled')
            samples = []
            for color in ('#ff0000', '#0000ff'):
                host.setStyleSheet('QWidget#jumpBackingTest { background: %s; }' % color)
                button.update()
                pump(app, .25)
                image = host.grab().toImage()
                ratio = image.devicePixelRatio()
                # Inside the backing but outside the arrow, away from antialiased edges.
                samples.append(image.pixelColor(round(20 * ratio), round(32 * ratio)))
                assert image.pixelColor(0, 0).name() == color
            assert samples[0] == samples[1], (theme, state, samples)
    host.close()


def run():
    assert splitMessage('a\n```py\nprint(1)\n```\nb') == [
        ('text', '', 'a\n'), ('code', 'py', 'print(1)'), ('text', '', 'b')]
    assert splitMessage('~~~js\nlet n = 1;') == [('code', 'js', 'let n = 1;')]
    assert splitMessage('````\na\n```\nb\n````\n') == [('code', '', 'a\n```\nb')]
    app = QApplication.instance() or QApplication([])
    chat = ChatWidget()
    chat.resize(860, 650)
    chat.show()
    assert isinstance(chat.jumpButton, RoundToolButton)
    assert chat.jumpButton.text() == '' and chat.jumpButton._icon == FluentIcon.DOWN
    assert chat.jumpButton.size().width() == 36 and chat.jumpButton.toolTip() == 'Jump to latest'
    tool = chat.addToolButton(FluentIcon.PHOTO, 'Caller label', side='left')
    right = QLabel('Right tool')
    chat.addToolWidget(right, side='right')
    assert chat.leftToolLayout.count() == 1 and chat.rightToolLayout.count() == 1
    assert tool.toolTip() == 'Caller label'
    pump(app)
    assert chat.splitter.orientation() == Qt.Vertical
    assert not chat.splitter.childrenCollapsible()
    handle = chat.splitter.handle(1)
    assert handle.height() == 6 and handle.cursor().shape() == Qt.SplitVCursor
    before = (chat.scrollArea.height(), chat.composer.height(), chat.inputEdit.height())
    dragDivider(chat, -110, app)
    assert chat.scrollArea.height() < before[0] - 80
    assert chat.composer.height() > before[1] + 80
    assert chat.inputEdit.height() > before[2] + 80
    assert chat.inputEdit.height() > 160  # No old maximum blocks the expanded input.
    sizes = chat.splitter.sizes()
    chat.setComposerVisible(False)
    pump(app)
    assert chat.composer.isHidden() and handle.isHidden()
    assert chat.scrollArea.height() == chat.height()
    chat.setComposerVisible(True)
    pump(app)
    assert handle.isVisible() and chat.splitter.sizes() == sizes
    dragDivider(chat, -10000, app)
    assert chat.scrollArea.height() >= 100 and chat.composer.isVisible()
    dragDivider(chat, 10000, app)
    assert chat.inputEdit.height() >= 76 and chat.scrollArea.isVisible()
    chat.splitter.setSizes([460, 184])
    try:
        chat.addToolWidget(QWidget(), side='invalid')
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid toolbar side accepted')
    user = chat.addMessage('Hello', role='user', name='Me', messageId='user')
    assistant = chat.addMessage('', name='Assistant', messageId='assistant', streaming=True)
    pump(app)
    assert not chat.isMessageToolBarEnabled()
    assert chat.messageToolBar(user).isHidden() and chat.messageToolBar(assistant).isHidden()
    bubbleWidth = chat._rows[user].bubble.width()
    chat.setMessageToolBarEnabled(True)
    pump(app)
    assert chat.messageToolBar(user).isVisible() and chat.messageToolBar(assistant).isVisible()
    assert list(chat.messageToolBar(user).buttons) == ['copy', 'share']
    assert list(chat.messageToolBar(assistant).buttons) == ['copy', 'retry', 'like', 'dislike', 'readAloud', 'share']
    assert chat._rows[user].bubble.width() == bubbleWidth  # bar never stretches short bubbles
    buttons = list(chat.messageToolBar(assistant).buttons.values())
    assert len({b.y() for b in buttons}) == 1  # all six fit on one line
    actionEvents = []
    chat.messageActionTriggered.connect(lambda action, messageId: actionEvents.append((action, messageId)))
    retryButton = chat.messageActionButton(assistant, 'retry')
    retryButton.click()
    assert actionEvents[-1] == ('retry', assistant)
    assert chat.messageActionButton(user, 'retry') is None
    chat.setMessageToolBarEnabled(False)
    pump(app)
    assert chat.messageToolBar(assistant).isHidden() and chat._rows[user].bubble.width() == bubbleWidth
    chat.setMessageToolBarEnabled(True)
    assert chat.messageActionButton(assistant, 'retry') is retryButton
    firstBlock = chat._rows[assistant].bubble.blocks[0][1]
    chat.appendText(assistant, '**Hello** ')
    chat.appendText(assistant, 'world')
    assert chat.message(assistant).content == '**Hello** world'
    pump(app)
    assert chat._rows[assistant].bubble.blocks[0][1] is firstBlock
    assert firstBlock.toPlainText() == 'Hello world'
    assert chat.messageActionButton(assistant, 'retry') is retryButton
    chat.messageActionButton(assistant, 'copy').click()
    assert QApplication.clipboard().text() == '**Hello** world'
    assert chat._rows[user].body.x() > chat._rows[assistant].body.x()
    chat.appendText(assistant, '\n\n```python\nprint("hello")')
    pump(app)
    code = chat._rows[assistant].bubble.blocks[-1][1]
    assert isinstance(code, _CodeBlock) and code.editor.toPlainText() == 'print("hello")'
    chat.appendText(assistant, '\n```\nDone.')
    chat.finishMessage(assistant)
    pump(app, .3)
    assert chat._rows[assistant].bubble.blocks[1][1] is code
    assert not chat.message(assistant).streaming and not chat._rows[assistant].statusLabel.isVisible()
    code.copyButton.click()
    assert QApplication.clipboard().text() == 'print("hello")'
    assert not any(name.startswith(('PySide6.QtWebEngine', 'PySide6.QtWebChannel')) for name in sys.modules)

    # Formula substitution, including literal inline code and custom providers.
    expressions = []
    def formula(expression, color, pointSize):
        expressions.append(expression)
        image = QImage(40, 20, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        return image
    chat.setFormulaRenderer(formula)
    maths = chat.addMessage(r'Inline $x^2$, literal `$y$` and display $$\frac{1}{2}$$')
    pump(app)
    browser = chat._rows[maths].bubble.blocks[0][1]
    assert '$y$' in browser.toPlainText() and 'MATH' not in browser.toPlainText()
    assert expressions == ['x^2', r'\frac{1}{2}']
    images = 0
    block = browser.document().begin()
    while block.isValid():
        iterator = block.begin()
        while not iterator.atEnd():
            images += iterator.fragment().charFormat().isImageFormat()
            iterator += 1
        block = block.next()
    assert images == 2
    # Exercise the actual offline formula renderer, including transparent pixels
    # and high-DPI sizing. No browser or external TeX process is involved.
    from qfluentwidgets_pro.common.chat_math import renderFormula
    real = renderFormula(r'\frac{-b \pm \sqrt{b^2-4ac}}{2a}', '#eeeeee')
    assert not real.isNull() and real.devicePixelRatio() == 2
    assert real.pixelColor(0, 0).alpha() == 0
    warnings = []
    chat.renderWarning.connect(warnings.append)
    chat.setFormulaRenderer(lambda *args: QImage())
    bad = chat.addMessage('$invalid$')
    assert '$invalid$' in chat._rows[bad].bubble.blocks[0][1].toPlainText() and warnings
    chat.setFormulaRenderer(formula)
    malicious = chat.addMessage('<img src="file:///private.png">\n\n![image](https://example.com/a.png)')
    security = chat._rows[malicious].bubble.blocks[0][1]
    assert security.loadResource(QTextDocument.ImageResource, None) is None
    assert '<img' in security.toPlainText()  # raw HTML is inert Markdown text

    sent = []
    chat.sendRequested.connect(sent.append)
    before = len(chat.messages())
    chat.inputEdit.setPlainText('  preserve spaces  ')
    QTest.keyClick(chat.inputEdit, Qt.Key_Return)
    assert sent == ['  preserve spaces  '] and len(chat.messages()) == before
    chat.inputEdit.setPlainText('first')
    QTest.keyClick(chat.inputEdit, Qt.Key_Return, Qt.ShiftModifier)
    assert '\n' in chat.inputEdit.toPlainText()
    chat.setBusy(True)
    chat.send()
    assert len(sent) == 1 and not chat.sendButton.isEnabled()
    chat.setBusy(False)
    chat.setSendOnEnter(False)
    QTest.keyClick(chat.inputEdit, Qt.Key_Return, Qt.ControlModifier)
    assert len(sent) == 2
    chat.inputEdit._preediting = True
    QTest.keyClick(chat.inputEdit, Qt.Key_Return, Qt.ControlModifier)
    assert len(sent) == 2
    chat.inputEdit._preediting = False

    image = QImage(300, 100, QImage.Format_ARGB32)
    image.fill(Qt.blue)
    imageId = chat.addImageMessage(image, role='user')
    widget = QLabel('Custom file card')
    widgetId = chat.addWidgetMessage(widget, name='Person')
    assert chat.message(imageId).kind == 'image' and chat.message(widgetId).kind == 'widget'
    assert list(chat.messageToolBar(imageId).buttons) == ['copy', 'share']
    assert list(chat.messageToolBar(widgetId).buttons) == ['share']
    pump(app)
    chat.messageActionButton(imageId, 'copy').click()
    pump(app)
    copiedImage = QApplication.clipboard().image()
    assert not copiedImage.isNull() and copiedImage.pixelColor(0, 0).blue() == 255
    custom = []
    chat.addMessageAction('inspect', FluentIcon.INFO, 'Caller inspect label', custom.append,
                          roles='assistant', kinds='text')
    assert chat.messageActionButton(user, 'inspect') is None
    chat.messageActionButton(assistant, 'inspect').click()
    assert custom == [assistant] and actionEvents[-1] == ('inspect', assistant)
    assert chat.messageActionButton(assistant, 'inspect').toolTip() == 'Caller inspect label'
    future = chat.addMessage('Future row', name='Assistant')
    assert chat.messageActionButton(future, 'inspect') is not None
    chat.removeMessageAction('inspect')
    assert chat.messageActionButton(future, 'inspect') is None
    try:
        chat.addMessageAction('invalid', FluentIcon.INFO, roles='nobody')
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid action filter accepted')
    for n in range(25):
        chat.addMessage('History ' + str(n))
    pump(app, .3)
    chat.scrollToBottom()
    bar = chat.scrollArea.verticalScrollBar()
    assert bar.maximum() > 0 and bar.value() == bar.maximum()
    bar.setValue(120)
    position = bar.value()
    chat.appendText(assistant, '\nAnother streaming update')
    chat.addMessage('Do not jump to bottom')
    pump(app, .3)
    assert bar.value() == position and chat.jumpButton.isVisible()
    dragDivider(chat, -90, app)
    assert bar.value() == position and chat.jumpButton.isVisible()
    assert chat.jumpButton.geometry().bottom() == chat.scrollArea.viewport().height() - 15
    chat.scrollToBottom()
    assert bar.value() == bar.maximum()
    dragDivider(chat, 90, app)
    assert bar.value() == bar.maximum() and not chat.jumpButton.isVisible()
    checkJumpBacking(chat, app)
    for theme in (Theme.DARK, Theme.LIGHT):
        setTheme(theme)
        pump(app)
        assert chat._rows[user].body.width() <= chat._maximumBubbleWidth
        handle._hovered = False
        normal = handle.grab().toImage()
        center = handle.rect().center()
        QApplication.sendEvent(handle, QEnterEvent(QPointF(center),
                              QPointF(handle.mapTo(chat.window(), center)),
                              QPointF(handle.mapToGlobal(center))))
        assert handle._hovered
        hovered = handle.grab().toImage()
        sample = QPoint(normal.width() // 2, round((handle.height() // 2) * normal.devicePixelRatio()))
        assert normal.pixelColor(sample) != hovered.pixelColor(sample)
        QApplication.sendEvent(handle, QEvent(QEvent.Leave))
        assert not handle._hovered
    chat.resize(380, 650)
    pump(app)
    assert chat.scrollArea.horizontalScrollBar().maximum() == 0
    for row in chat._rows.values():
        toolbar = row.messageToolBar
        for button in toolbar.buttons.values():
            assert button.geometry().right() < toolbar.width()
            assert button.geometry().bottom() < toolbar.height()
    chat.clearMessageActions()
    pump(app)
    assert chat.messageToolBar(user).isHidden() and chat.isMessageToolBarEnabled()
    chat.removeMessage(assistant)
    chat.clear()
    pump(app)
    assert not chat.messages() and chat.leftToolLayout.count() == 1
    chat.close()
    print('PASS: native chat alignment, tools, streaming/code reuse, Markdown safety, formulas, '
          'copy, IME/send shortcuts, images/custom cards, scrolling, message action bars, '
          'opaque round jump button, draggable divider and both themes')


if __name__ == '__main__':
    run()
