"""Native light/dark toolbox previews, including the alternate expanded panel."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from qfluentwidgets_pro import Theme, setTheme
from gallery_fixtures.tool_box_demo import ToolBoxDemo

app = QApplication([])
demo = ToolBoxDemo()
demo.resize(700, 650)
demo.show()
output = Path(tempfile.mkdtemp(prefix='fluent-tool-box-'))
for theme, name in ((Theme.DARK, 'dark'), (Theme.LIGHT, 'light')):
    setTheme(theme)
    for index in (0, 1):
        demo.toolBox.setCurrentIndex(index)
        QTest.qWait(450)  # A switch closes the old page before opening the new one.
        path = output / (name + '-' + str(index) + '.png')
        assert demo.grab().save(str(path))
        print(path)
    demo.toolBox.setCurrentIndex(-1)
    QTest.qWait(250)
    header = demo.toolBox.itemHeader(0)
    header.clearFocus()
    QTest.mouseMove(header, header.arrowRect().center())
    QTest.qWait(50)
    path = output / (name + '-hover.png')
    assert demo.grab().save(str(path))
    print(path)
demo.close()
