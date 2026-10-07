"""Gallery chat launcher: py -3.9 tests/check_chat_window.py [--native]."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if '--native' not in sys.argv:
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from gallery.common.config import cfg, Language
from main import createApplication, MainWindow
from qfluentwidgets_pro import Theme, setTheme
from qfluentwidgets_pro.window.fluent_window import FluentWidget


def run():
    cfg.language.value = Language.CHINESE_SIMPLIFIED
    app = createApplication([])
    host = MainWindow()
    host.show()
    host.navigationInterface.expand(useAni=False)
    QTest.qWait(200)
    try:
        selected = host.stackedWidget.currentWidget()
        button = host.navigationInterface.widget('chat')
        QTest.mouseClick(button.itemWidget, Qt.LeftButton)
        window = host._chatWindow
        assert isinstance(window, FluentWidget)
        assert window.isVisible() and window.isWindow() and window.parentWidget() is None
        assert window.windowFlags() & Qt.WindowType_Mask == Qt.Window
        assert window.windowTitle().endswith('聊天')
        assert host.stackedWidget.currentWidget() is selected
        assert not any(n.startswith('PySide6.QtWebEngine') for n in sys.modules)
        flags = window.windowFlags()
        chat = window.chat
        assert len(chat.messages()) == 6 and chat.isMessageToolBarEnabled()
        QTest.qWait(200)
        # Send through the real composer, then close during simulated streaming.
        chat.inputEdit.setPlainText('Local message')
        chat.send()
        QTest.qWait(150)
        assert window.demo.timer.isActive()
        messageId = window.demo._streamId
        assert chat.message(messageId).content
        QTest.mouseClick(window.titleBar.closeBtn, Qt.LeftButton)
        assert not window.isVisible() and host.isVisible()
        assert not window.demo.timer.isActive() and window.demo._streamId is None
        assert not chat.message(messageId).streaming
        history = chat.messages()
        button.click()
        assert host._chatWindow is window and window.isVisible()
        assert chat.messages() == history, (history, chat.messages())
        # Qt can release/recreate a plain QWidget's HWND on close/show. The
        # Python window and messages must survive, with the native flags intact.
        assert window.winId() and window.windowFlags() == flags
        # Mica cannot be captured by QWidget.grab; preview its solid fallback.
        window.setMicaEffectEnabled(False)
        output = Path(tempfile.mkdtemp(prefix='fluent-chat-window-'))
        for theme in (Theme.DARK, Theme.LIGHT):
            setTheme(theme)
            QTest.qWait(200)
            assert window.demo.y() >= window.titleBar.height()
            assert window.grab().save(str(output / (theme.value.lower() + '.png')))
        window.demo._reset()
        assert len(chat.messages()) == 6
        host.close()
        assert not window.isVisible() and not window.demo.timer.isActive()
        print('PASS: sidebar click, native independent window, translations, local streaming, close/stop/reopen/history, themes and shutdown')
        print('Previews:', output)
    finally:
        host.close()
        app.processEvents()


if __name__ == '__main__':
    run()
