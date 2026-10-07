import os
import sys

if sys.platform == "win32":
    args = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--windows-disable-console",
        "--plugin-enable=pyside6",
        "--include-qt-plugins=sensible,sqldrivers",
        "--assume-yes-for-downloads",
        "--mingw64",
        "--show-memory",
        "--show-progress",
        # 排除未使用的重型库，减小打包体积
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=PySide6.QtPositioning",
        "--nofollow-import-to=PySide6.QtPrintSupport",
        "--nofollow-import-to=PySide6.QtOpenGL",
        "--noinclude-qt-translations",
        "main.py",
    ]

elif sys.platform == "darwin":
    args = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--plugin-enable=pyside6",
        "--show-memory",
        "--show-progress",
        "--macos-create-app-bundle",
        "--assume-yes-for-download",
        "--macos-disable-console",
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=PySide6.QtPrintSupport",
        "--noinclude-qt-translations",
        "main.py",
    ]
else:
    args = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--plugin-enable=pyside6",
        "--include-qt-plugins=sensible,sqldrivers",
        "--assume-yes-for-downloads",
        "--show-memory",
        "--show-progress",
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=scipy",
        "--noinclude-qt-translations",
        "main.py",
    ]


# Navigation indirectly references Acrylic. Exclude its optional CPU blur backend
# independently of chat formulas; the non-blurred fallback remains usable.
args.append("--nofollow-import-to=qfluentwidgets_pro.common.image_utils")

# Chat uses optional code highlighting and offline MathText formulas.
args = [arg for arg in args if arg != "--nofollow-import-to=numpy"]
args.append("--include-package=pygments")
args.append("--include-package=matplotlib")
args.append("--include-module=gallery.view.chat_interface")
# Pro preview factories use importlib; include them even before first use.
args.append("--include-package=gallery.pro_demos")
args.append("--include-qt-plugins=multimedia")
args.append("--include-data-files=gallery/resource/audio/waveform_sample.wav=gallery/resource/audio/waveform_sample.wav")
# Include the lazy chart window. Nuitka's PySide6 plugin detects its WebEngine
# imports and bundles the renderer executable and resource files automatically.
args.append("--include-package=gallery.view.chart")
os.system(" ".join(args))
print("打包完成！")
