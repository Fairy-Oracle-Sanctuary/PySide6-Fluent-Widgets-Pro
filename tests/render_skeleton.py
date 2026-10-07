"""Capture deterministic native skeleton frames for visual QA."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QLocale
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import FluentTranslator, Theme, setTheme
from gallery_fixtures.skeleton_demo import SkeletonDemo


def run():
    app = QApplication([])
    translator = FluentTranslator(QLocale('zh_CN'))
    app.installTranslator(translator)
    output = Path(tempfile.mkdtemp(prefix='fluent-skeleton-'))
    demo = SkeletonDemo()
    demo.resize(1000, 900)
    demo.show()
    for theme, name in ((Theme.DARK, 'dark'), (Theme.LIGHT, 'light')):
        setTheme(theme)
        QTest.qWait(40)
        for phase, suffix in ((0., 'base'), (.45, 'shimmer')):
            for skeleton in demo.skeletons:
                skeleton._animation.pause()
                skeleton._setPhase(phase)
            app.processEvents()
            path = output / (name + '-' + suffix + '.png')
            assert demo.grab().save(str(path))
            print(path)
    demo.close()


if __name__ == '__main__':
    run()
