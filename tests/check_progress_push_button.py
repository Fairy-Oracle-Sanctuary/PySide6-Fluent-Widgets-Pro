"""Run with py -3.9 tests/check_progress_push_button.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from qfluentwidgets_pro import ProgressPushButton, Theme, setTheme, setThemeColor


def run():
    app = QApplication([])
    button = ProgressPushButton('Download')
    button.resize(150, 40)
    button.show()
    app.processEvents()
    button.click()
    assert not button.isProgressing()
    button.setAutoProgressEnabled(True)
    button.click()
    assert button.isProgressing()
    stops = []
    button.stopRequested.connect(lambda: stops.append(True))
    button.click()
    assert stops == [True] and button.isProgressing()
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        setThemeColor('#8764b8')
        for value in (-5, 50, 120):
            button.setValue(value)
            QTest.qWait(180)
            expected = max(0, min(100, value))
            assert button.value() == expected and button.displayValue == expected
            image = button.grab().toImage()
            center = image.pixelColor(image.width() // 2, image.height() // 2)
            assert center.lightness() > 240 if theme == Theme.LIGHT else center.lightness() < 15
    assert button.isProgressing()
    button.setProgressing(False)
    assert button.text() == 'Download'
    button.setAutoProgressEnabled(False)
    button.click()
    assert not button.isProgressing()
    button.close()
    print('PASS: states, click policy, stop request, progress, themes and paint')


if __name__ == '__main__':
    run()
