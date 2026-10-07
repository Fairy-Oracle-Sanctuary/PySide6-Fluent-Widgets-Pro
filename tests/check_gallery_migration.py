"""Free gallery navigation, resources and lazy chart launcher (no WebEngine)."""
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget
from gallery.common.config import cfg, Language
from main import createApplication, MainWindow
from qfluentwidgets_pro import FluentWindow, Theme, setTheme


def run():
    # Set in memory only, without changing the user's saved gallery settings.
    cfg.language.value = Language.CHINESE_SIMPLIFIED
    app = createApplication([])
    window = MainWindow()
    window.show()
    QTest.qWait(100)
    try:
        assert isinstance(window, FluentWindow)
        assert window.stackedWidget.count() == 14
        assert not hasattr(window, 'buttonsInterface')
        assert not hasattr(window, '_chartWindow')
        assert not any(name.startswith('PySide6.QtWebEngine') for name in sys.modules)
        assert 'qfluentwidgets_pro.components.widgets.chat_widget' not in sys.modules
        button = window.navigationInterface.widget('charts')
        assert button.text() == '图表'
        assert not button.isSelectable
        chatButton = window.navigationInterface.widget('chat')
        assert chatButton.text() == '聊天' and not chatButton.isSelectable
        routes = list(window.navigationInterface.panel.items)
        assert routes.index('chat') == routes.index('charts') + 1
        assert not hasattr(window, '_chatWindow')
        for theme in (Theme.DARK, Theme.LIGHT):
            setTheme(theme)
            for i in range(window.stackedWidget.count()):
                page = window.stackedWidget.widget(i)
                window.switchTo(page)
                QTest.qWait(20)
                assert page.isVisible(), page.objectName()
                assert window.navigationInterface.widget(page.objectName()).text()

        class FakeChartWindow(QWidget):
            def setMicaEffectEnabled(self, enabled):
                self.micaRequested = enabled

        module = ModuleType('gallery.view.chart.home_interface')
        module.ChartMainWindow = FakeChartWindow
        with patch.dict(sys.modules, {module.__name__: module}):
            selected = window.stackedWidget.currentWidget()
            button.click()
            chart = window._chartWindow
            assert chart.isVisible() and chart.isWindow()
            assert chart.parentWidget() is None and chart.micaRequested
            assert window.stackedWidget.currentWidget() is selected
            chart.close()
            button.click()
            assert window._chartWindow is chart and chart.isVisible()
            window.close()
            assert not chart.isVisible()
        print('PASS: 14 migrated pages, both themes, Chinese resources, lazy independent/reusable chart launcher')
    finally:
        window.close()
        app.processEvents()


if __name__ == '__main__':
    run()
