"""Verify resting Fluent fills without changing existing interaction colors."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import FilledPushButton, FilledToolButton, Theme, setTheme


def run():
    app = QApplication([])
    expected = {'information': '#8a8a8a', 'success': '#0f7b0f',
                'warning': '#9d5d00', 'error': '#c42b1c'}
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        dark = theme == Theme.DARK
        for cls in (FilledPushButton, FilledToolButton):
            button = cls()
            button.resize(120, 32)
            for scheme in (*expected, 'attention'):
                button.setColorScheme(scheme)
                QTest.qWait(140)
                colors = button._getSchemeColors(dark)
                assert colors['bg'][1] == (QColor(255, 255, 255, 67) if dark else QColor(0, 0, 0, 60))
                assert colors['bg'][2] == (QColor(255, 255, 255, 30) if dark else QColor(0, 0, 0, 100))
                assert colors['border'][1] == (QColor(255, 255, 255, 150) if dark else QColor(0, 0, 0, 128))
                assert colors['border'][2] == (QColor(255, 255, 255, 30) if dark else QColor(0, 0, 0, 0))
                assert colors['text'] == QColor('white')
                if not dark and scheme in expected:
                    assert colors['bg'][0] == QColor(expected[scheme])
                    image = button.grab().toImage()
                    scale = image.devicePixelRatio()
                    assert image.pixelColor(round(8 * scale), round(16 * scale)) == colors['bg'][0]
            button.deleteLater()
            app.processEvents()
    print('Filled button resting colors and original interaction colors: OK')


if __name__ == '__main__':
    run()
