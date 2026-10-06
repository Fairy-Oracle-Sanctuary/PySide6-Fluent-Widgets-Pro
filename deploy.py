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
        "--nofollow-import-to=PySide6.QtWebChannel",
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
# as well as numpy/scipy above; the existing non-blurred fallback remains usable.
args.append("--nofollow-import-to=qfluentwidgets_pro.common.image_utils")

# This script packages main.py, whose gallery explicitly uses CodeEdit.
# Pygments discovers lexers dynamically, so include them for this gallery build.
# Do not copy this include into a business app that does not use CodeEdit.
args.append("--include-package=pygments")
# The waveform gallery explicitly uses QtMultimedia and offers a bundled WAV.
args.append("--include-qt-plugins=multimedia")
args.append("--include-data-files=gallery/resource/audio/waveform_sample.wav=gallery/resource/audio/waveform_sample.wav")
# Full-gallery ChatWidget formulas need Matplotlib/NumPy. CPU Acrylic blur is
# still excluded independently; plain-chat business apps can exclude both.
args.remove("--nofollow-import-to=numpy")
args.append("--include-package=matplotlib")
os.system(" ".join(args))
print("打包完成！")
