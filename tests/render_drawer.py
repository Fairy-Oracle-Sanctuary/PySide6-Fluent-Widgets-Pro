"""Render native drawer previews in all four directions and both themes."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QLocale
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import DrawerPosition, FluentTranslator, Theme, setTheme
from gallery_fixtures.drawer_demo import DrawerDemo


def run():
    app = QApplication([])
    translator = FluentTranslator(QLocale('zh_CN'))
    app.installTranslator(translator)
    output = Path(tempfile.mkdtemp(prefix='fluent-drawer-'))
    demo = DrawerDemo()
    demo.resize(1000, 820)
    demo.show()
    demo.drawer.setAnimationDuration(0)
    for theme, name in ((Theme.DARK, 'dark'), (Theme.LIGHT, 'light')):
        setTheme(theme)
        QTest.qWait(350)
        for position in DrawerPosition:
            demo.drawer.setDrawerSize(320 if position in (DrawerPosition.LEFT, DrawerPosition.RIGHT) else 240)
            demo.drawer.open(position)
            QTest.qWait(50)
            path = output / (name + '-' + position.value + '.png')
            assert demo.grab().save(str(path))
            print(path)
            demo.drawer.hide()
    demo.close()


if __name__ == '__main__':
    run()
