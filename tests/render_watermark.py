"""Capture native watermark demo previews in both themes."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import Theme, setTheme
from gallery.view.watermark_demo import WatermarkDemo


def run():
    app = QApplication([])
    output = Path(tempfile.mkdtemp(prefix='fluent-watermark-'))
    demo = WatermarkDemo()
    demo.resize(1000, 980)
    demo.show()
    for theme, name in ((Theme.DARK, 'dark'), (Theme.LIGHT, 'light')):
        setTheme(theme)
        QTest.qWait(350)  # Let CardWidget's theme-transition colors settle.
        path = output / (name + '.png')
        assert demo.grab().save(str(path))
        print(path)
    demo.close()


if __name__ == '__main__':
    run()
