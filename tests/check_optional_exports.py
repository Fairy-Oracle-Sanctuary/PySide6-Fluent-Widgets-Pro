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
for name in ("CodeEdit", "CodeLanguage", "ChartWidget", "AcrylicLabel", "MediaPlayer", "VideoWidget"):
    assert not hasattr(q, name), name
assert "qfluentwidgets_pro.components.widgets.code_edit" not in sys.modules
assert "qfluentwidgets_pro.components.widgets.chart_widget" not in sys.modules
assert "qfluentwidgets_pro.multimedia" not in sys.modules
from qfluentwidgets_pro.components.widgets.acrylic_label import isAcrylicAvailable
assert not isAcrylicAvailable  # documented navigation fallback when blur is excluded
from qfluentwidgets_pro.components.widgets.code_edit import CodeEdit, CodeLanguage
assert CodeLanguage.JSON and "pygments" not in sys.modules
from PySide6.QtWidgets import QApplication
app = QApplication([])
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
    print("PASS: all three gallery build profiles exclude CPU blur; no compiler was invoked")


if __name__ == "__main__":
    run()
