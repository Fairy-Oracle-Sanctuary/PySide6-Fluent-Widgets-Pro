"""Render light/dark native dashboard card examples for visual verification."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import Theme, setTheme
from gallery_fixtures.dashboard_card_demo import DashboardCardDemo


app = QApplication([])
demo = DashboardCardDemo()
demo.resize(900, 650)
demo.show()
output = Path(tempfile.mkdtemp(prefix='fluent-dashboard-card-'))
for theme, name in ((Theme.DARK, 'dark'), (Theme.LIGHT, 'light')):
    setTheme(theme)
    QTest.qWait(350)
    path = output / (name + '.png')
    assert demo.grab().save(str(path))
    print(path)
demo.close()
