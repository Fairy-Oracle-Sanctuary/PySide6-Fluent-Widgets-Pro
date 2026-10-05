"""Run with py -3.9 tests/check_progress_toast.py [preview-directory]."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QAbstractAnimation
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import (
    InfoBarIcon, ProgressToast, Theme, Toast, ToastManager, ToastPosition,
    setTheme, setThemeColor, themeColor,
)


def pixel(image, x, y):
    scale = image.devicePixelRatio()
    return image.pixelColor(round(x * scale), round(y * scale))


def checkPaint(bar):
    bar.setGraphicsEffect(None)
    image = bar.grab().toImage()
    color = bar.barColor()
    assert pixel(image, bar.width() * .5, 2) != color  # no Toast top stripe
    assert pixel(image, 20, bar.height() - 1) == color
    if bar.value() < 100:
        assert pixel(image, bar.width() * .95, bar.height() - 2) != color
    # Sample inside the SVG disk, away from its white/black glyph.
    point = bar.iconWidget.mapTo(bar, bar.iconWidget.rect().topLeft())
    assert pixel(image, point.x() + 3, point.y() + 8) == color
    assert pixel(image, 0, bar.height() - 1).alpha() == 0


def run():
    app = QApplication([])
    owners = [QWidget(), QWidget()]
    for owner in owners:
        owner.resize(1000, 800)
        owner.show()
    setTheme(Theme.LIGHT)
    done = ProgressToast.success("文件下载成功", parent=owners[0])
    downloading = ProgressToast.warning("正在下载文件，请耐心等待...", value=77, parent=owners[0])
    QTest.qWait(250)
    assert done.value() == 100 and downloading.value() == 77
    assert done.duration == -1 and downloading.duration == -1
    assert done.height() == downloading.height() == 50
    assert done.width() >= 280 and downloading.width() >= 280
    assert done.barColor().name() == "#0f7b0f"
    assert downloading.barColor().name() == "#9d5d00"
    assert downloading.y() > done.y()
    checkPaint(done)
    checkPaint(downloading)

    downloading.setStateColor(InfoBarIcon.WARNING, "#8844cc", "#cc88ff")
    downloading.setStateColor(InfoBarIcon.SUCCESS, "#0066aa", "#55ccff")
    for theme, warningColor, successColor in (
        (Theme.LIGHT, "#8844cc", "#0066aa"),
        (Theme.DARK, "#cc88ff", "#55ccff"),
    ):
        setTheme(theme)
        downloading.setIcon(InfoBarIcon.WARNING)
        assert downloading.barColor().name() == warningColor
        checkPaint(downloading)
        downloading.setIcon(InfoBarIcon.SUCCESS)
        assert downloading.barColor().name() == successColor
        checkPaint(downloading)
    downloading.setCustomBarColor("#223344")
    downloading.setIcon(InfoBarIcon.ERROR)
    assert downloading.barColor().name() == "#223344"
    downloading.setIcon(InfoBarIcon.SUCCESS)
    assert downloading.barColor().name() == "#55ccff"  # state override wins
    downloading.setStateColor(InfoBarIcon.WARNING, "#aa6600")
    downloading.setIcon(InfoBarIcon.WARNING)
    assert downloading.barColor().name() == "#aa6600"
    for invalid in ("not-a-color", "#oops"):
        try:
            downloading.setStateColor(InfoBarIcon.WARNING, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid color accepted")

    changes = []
    downloading.valueChanged.connect(changes.append)
    downloading.setValue(10)
    assert downloading.value() == 10
    assert downloading._progressAni.state() == QAbstractAnimation.Running
    QTest.qWait(60)
    assert 10 < downloading.progress < 77
    downloading.setValue(40)
    QTest.qWait(180)
    assert downloading.progress == 40
    downloading.setUseAni(False)
    downloading.setValue(200)
    assert downloading.value() == 100 and downloading.progress == 100
    assert downloading.icon() == InfoBarIcon.WARNING and downloading.isVisible()
    downloading.setValue(-5)
    assert downloading.value() == 0
    assert changes == [10, 40, 100, 0]
    downloading.setContent("")
    assert downloading.contentLabel.isHidden()
    downloading.setContent("Longer task message\nSecond line\nThird line")
    assert downloading.height() > 50 and not downloading.contentLabel.isHidden()
    QTest.qWait(250)
    assert downloading.pos() == downloading.manager.slideEndPos(downloading)

    ordinary = Toast.info("Plain Toast", "Shares the stack", duration=-1, parent=owners[0])
    isolated = ProgressToast.info("Other window", parent=owners[1])
    QTest.qWait(250)
    assert ordinary.y() > downloading.y() + downloading.height()
    assert isolated.y() == done.y()
    oldY = downloading.y()
    closed = []
    done.closed.connect(lambda: closed.append(True))
    done.closeButton.click()
    QTest.qWait(250)
    assert closed == [True] and downloading.y() < oldY
    for bar in (downloading, ordinary, isolated):
        bar.close()
    QTest.qWait(30)

    bars = []
    for position in ToastPosition:
        bar = ProgressToast.error("Task failed", value=50, position=position, parent=owners[0])
        bars.append(bar)
    QTest.qWait(250)
    owners[0].resize(1200, 900)
    QTest.qWait(50)
    for bar in bars:
        assert bar.pos() == bar.manager.slideEndPos(bar)
        bar.close()
    QTest.qWait(30)

    neutral = ProgressToast.info("Working", isClosable=False, parent=owners[0])
    setThemeColor("#1f9faa")
    assert neutral.barColor() == themeColor() and neutral.closeButton.isHidden()
    neutral.close()
    custom = ProgressToast.custom("Custom", "#336699", value=50, parent=owners[0])
    assert custom.barColor().name() == "#336699"
    custom.close()
    auto = ProgressToast.success("Auto close", duration=30, parent=owners[0])
    autoClosed = []
    auto.closed.connect(lambda: autoClosed.append(True))
    QTest.qWait(60)
    assert autoClosed == [True]

    if len(sys.argv) > 1:
        setTheme(Theme.LIGHT)
        for name, bar in (
            ("progress-toast-success", ProgressToast.success("文件下载成功", parent=owners[0])),
            ("progress-toast-warning", ProgressToast.warning("正在下载文件，请耐心等待...", value=77, parent=owners[0])),
        ):
            QTest.qWait(250)
            bar.grab().save(str(Path(sys.argv[1]) / (name + ".png")))
            print(name, "logical size:", bar.width(), bar.height())
            bar.close()
    QTest.qWait(30)
    for position in ToastPosition:
        assert not ToastManager.get(position).toastInfoBars
    for owner in owners:
        owner.close()
    print("PASS: paint, custom state colors, themes, animated values, messages, mixed stacks, window isolation, positions and close")


if __name__ == "__main__":
    run()
