"""Check optional import boundaries without running a Nuitka compilation."""
import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def run():
    script = f'''
import sys
from importlib.abc import MetaPathFinder
sys.path.insert(0, {str(ROOT)!r})
class BlockOptional(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        blocked = ("numpy", "scipy", "PIL", "colorthief", "pygments",
                   "PySide6.QtWebEngine", "PySide6.QtQuick", "PySide6.QtQml",
                   "PySide6.QtMultimedia", "qfluentwidgets_pro.common.image_utils")
        if any(fullname == name or fullname.startswith(name + ".")
               or (name.startswith("PySide6.") and fullname.startswith(name))
               for name in blocked):
            raise ImportError("Optional dependency blocked by regression test: " + fullname)
sys.meta_path.insert(0, BlockOptional())
import qfluentwidgets_pro as q
assert hasattr(q, "RadialGauge")
assert hasattr(q, "RangeCalendarPicker") and hasattr(q, "FastRangeCalendarPicker")
assert hasattr(q, "CalendarTimePicker") and hasattr(q, "FastCalendarTimePicker")
assert hasattr(q, "AudioWaveformWidget")
assert hasattr(q, "CircleColorPicker")
assert hasattr(q, "ScreenColorPicker")
assert hasattr(q, "DropDownColorPalette")
assert hasattr(q, "DropDownColorPicker")
assert hasattr(q, "ShortcutPicker")
assert hasattr(q, "WaitingDialog")
assert hasattr(q, "MenuBar")
assert hasattr(q, "GuideWindow")
assert hasattr(q, "RoundTabBar")
assert hasattr(q, "RoundTabWidget")
for name in ("CodeEdit", "CodeLanguage", "ChartWidget", "AcrylicLabel", "MediaPlayer", "VideoWidget", "AudioDecoder"):
    assert not hasattr(q, name), name
assert "qfluentwidgets_pro.components.widgets.code_edit" not in sys.modules
assert "qfluentwidgets_pro.components.widgets.chart_widget" not in sys.modules
assert "qfluentwidgets_pro.multimedia" not in sys.modules
assert "qfluentwidgets_pro.common.audio_decoder" not in sys.modules
from qfluentwidgets_pro.components.widgets.acrylic_label import isAcrylicAvailable
assert not isAcrylicAvailable  # documented navigation fallback when blur is excluded
from qfluentwidgets_pro.components.widgets.code_edit import CodeEdit, CodeLanguage
assert CodeLanguage.JSON and "pygments" not in sys.modules
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor
app = QApplication([])
from PySide6.QtWidgets import QWidget
waitingOwner = QWidget()
menuBar = q.MenuBar(waitingOwner)
assert menuBar.addMenu('File').title() == 'File'
guideWindow = q.GuideWindow()
assert guideWindow.addPage(QWidget()) == 0 and guideWindow.currentIndex() == 0
roundTabBar = q.RoundTabBar()
roundTabBar.addTab('lightweight', 'Tab')
assert roundTabBar.currentTab().routeKey() == 'lightweight'
roundTabWidget = q.RoundTabWidget()
assert roundTabWidget.addTab(QWidget(), 'Page') == 0
assert isinstance(roundTabWidget.tabBar(), q.RoundTabBar)
waitingDialog = q.WaitingDialog('Please wait...', 'Preparing task...', waitingOwner)
assert waitingDialog.title() == 'Please wait...'
assert waitingDialog.content() == 'Preparing task...'
shortcutPicker = q.ShortcutPicker()
shortcutPicker.setKeySequence("Alt+F8")
assert shortcutPicker.keySequence().toString() == "Alt+F8"
colorPicker = q.CircleColorPicker(["red", "blue"])
colorPicker.setColor("blue")
assert colorPicker.currentIndex() == 1
screenPicker = q.ScreenColorPicker("red")
screenPicker.setColor("blue")
assert screenPicker.color().name() == "#0000ff" and not screenPicker.isPicking()
dropDownPalette = q.DropDownColorPalette("red")
dropDownPalette.setColor("blue")
assert dropDownPalette.color().name() == "#0000ff"
dropDownPicker = q.DropDownColorPicker("red")
dropDownPicker.setColor("#800000ff")
assert dropDownPicker.color().name(QColor.HexArgb) == "#800000ff"
waveform = q.AudioWaveformWidget()
waveform.setSamples([-.5, .5, 0], 24000)
waveform.appendSamples([0], 24000)
assert waveform.sampleCount() == 4
assert not any(name.startswith("PySide6.QtMultimedia") for name in sys.modules)
try:
    CodeEdit()
except ImportError as error:
    assert "Pygments" in str(error)
else:
    raise AssertionError("Missing Pygments did not produce a useful error")
print("PASS: lightweight root import with optional dependencies excluded, explicit CodeEdit and Acrylic fallback")
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                            capture_output=True, text=True)
    print(result.stdout)
    if result.returncode:
        raise AssertionError(result.stderr)
    for platform in ("win32", "darwin", "linux"):
        with patch("os.system", return_value=0) as command, patch("sys.platform", platform):
            runpy.run_path(str(ROOT / "deploy.py"))
        args = command.call_args.args[0]
        assert "--nofollow-import-to=qfluentwidgets_pro.common.image_utils" in args
        assert "--nofollow-import-to=numpy" in args
        assert "--nofollow-import-to=scipy" in args
        assert "--include-package=pygments" in args  # full gallery intentionally uses it
        assert "--include-qt-plugins=multimedia" in args
        assert "--include-data-files=gallery/resource/audio/waveform_sample.wav=gallery/resource/audio/waveform_sample.wav" in args
    print("PASS: all three gallery build profiles exclude CPU blur; no compiler was invoked")


if __name__ == "__main__":
    run()
