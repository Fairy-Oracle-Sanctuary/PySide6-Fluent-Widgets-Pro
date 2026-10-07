"""Render the native gallery page for visual QA, without screen automation."""
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QEvent, QLocale, QPointF
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import FluentTranslator, Theme, setTheme
from gallery_fixtures.chat_widget_demo import ChatWidgetDemo


def run():
    app = QApplication([])
    translator = FluentTranslator(QLocale('zh_CN'))
    app.installTranslator(translator)
    output = Path(tempfile.mkdtemp(prefix='fluent-chat-'))
    demo = ChatWidgetDemo()
    demo.resize(1040, 840)
    demo.show()
    for theme, name in ((Theme.DARK, 'dark'), (Theme.LIGHT, 'light')):
        setTheme(theme)
        demo.setStyleSheet('ChatWidgetDemo { background: %s; }' % ('#202020' if name == 'dark' else '#ffffff'))
        until = time.monotonic() + .7
        while time.monotonic() < until:
            app.processEvents()
            time.sleep(.005)
        demo.chat.scrollArea.verticalScrollBar().setValue(0)
        app.processEvents()
        path = output / (name + '.png')
        assert demo.grab().save(str(path))
        print(path)
        sizes = demo.chat.splitter.sizes()
        demo.chat.splitter.setSizes([sizes[0] - 130, sizes[1] + 130])
        app.processEvents()
        divider = demo.chat.splitter.handle(1)
        center = divider.rect().center()
        QApplication.sendEvent(divider, QEnterEvent(QPointF(center),
                              QPointF(divider.mapTo(demo, center)),
                              QPointF(divider.mapToGlobal(center))))
        app.processEvents()
        path = output / (name + '-expanded.png')
        assert demo.grab().save(str(path))
        print(path)
        QApplication.sendEvent(divider, QEvent(QEvent.Leave))
        demo.chat.splitter.setSizes(sizes)
    assert not any(n.startswith(('PySide6.QtWebEngine', 'PySide6.QtWebChannel')) for n in sys.modules)
    demo.close()


if __name__ == '__main__':
    run()
