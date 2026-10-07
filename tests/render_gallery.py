"""Render the migrated native gallery in light/dark Chinese UI."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from gallery.common.config import cfg, Language
from main import createApplication, MainWindow
from qfluentwidgets_pro import Theme, setTheme

cfg.language.value = Language.CHINESE_SIMPLIFIED
app = createApplication([])
window = MainWindow()
# DWM's Mica pixels aren't captured by QWidget.grab(); render the solid fallback.
window.setMicaEffectEnabled(False)
window.resize(1200, 850)
window.show()
output = Path(tempfile.mkdtemp(prefix='fluent-gallery-'))
try:
    for theme, name in ((Theme.DARK, 'dark'), (Theme.LIGHT, 'light')):
        setTheme(theme)
        window.navigationInterface.expand(useAni=False)
        for page, suffix in ((window.homeInterface, 'home'),
                             (window.basicInputInterface, 'input')):
            window.switchTo(page)
            QTest.qWait(500)
            path = output / f'{name}-{suffix}.png'
            assert window.grab().save(str(path))
            print(path, flush=True)
finally:
    window.close()
