"""Run with py -3.9 tests/check_round_progress_toast.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QAbstractAnimation
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import (
    IndeterminateProgressRing, ProgressToast, RoundProgressToast,
    Theme, ToastManager, ToastPosition, setTheme, setThemeColor, themeColor,
)


def pixel(image, x, y):
    scale = image.devicePixelRatio()
    return image.pixelColor(round(x * scale), round(y * scale))


def run():
    app = QApplication([])
    owners = [QWidget(), QWidget()]
    for owner in owners:
        owner.resize(1000, 800)
        owner.show()
    bar = RoundProgressToast.new(parent=owners[0])
    ring = bar.progressRing
    assert isinstance(ring, IndeterminateProgressRing)
    assert bar.duration == -1 and bar.closeButton.isHidden()
    assert ring.width() == 20 and ring.getStrokeWidth() == 3
    assert ring.aniGroup.duration() == 2000 and ring.aniGroup.loopCount() == -1
    QTest.qWait(250)
    assert bar.content == 'Loading, please wait'
    # English/localized defaults may be wider than the compact minimum.
    assert bar.width() >= 180 and bar.height() == 48
    assert ring.startAngle > 0 and ring.spanAngle > 0
    bar.hide()
    time = ring.aniGroup.currentTime()
    assert ring.aniGroup.state() == QAbstractAnimation.Paused
    QTest.qWait(40)
    assert ring.aniGroup.currentTime() == time
    bar.show()
    QTest.qWait(40)
    assert ring.aniGroup.state() == QAbstractAnimation.Running
    assert ring.aniGroup.currentTime() > time
    owners[0].hide()
    assert ring.aniGroup.state() == QAbstractAnimation.Paused
    owners[0].show()
    assert ring.aniGroup.state() == QAbstractAnimation.Running

    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        for accent in ("#22ddec", "#a855f7"):
            setThemeColor(accent)
            QTest.qWait(30)
            assert ring.lightBarColor() == ring.darkBarColor() == themeColor()
            bar.setGraphicsEffect(None)
            image = bar.grab().toImage()
            expected = "#f7f7f7" if theme == Theme.LIGHT else "#272727"
            assert pixel(image, bar.width() / 2, 5).name() == expected
            assert pixel(image, bar.width() / 2, bar.height() - 3).name() == expected
            assert pixel(image, 0, 0).alpha() == 0
            assert pixel(image, 2, bar.height() / 2).name() == expected
    second = ProgressToast.success("Another notification", parent=owners[0])
    isolated = RoundProgressToast.new(parent=owners[1])
    QTest.qWait(250)
    assert isolated.y() == bar.y()
    oldY = second.y()
    bar.setContent("First line\nSecond line\nThird line")
    QTest.qWait(250)
    assert bar.height() > 48 and second.y() > oldY
    assert second.pos() == second.manager.slideEndPos(second)
    bar.setContent("")
    assert bar.contentLabel.isHidden()
    bar.setContent("加载中，请稍候")
    assert not bar.contentLabel.isHidden() and bar.height() == 48
    closed = []
    bar.closed.connect(lambda: closed.append(ring.aniGroup.state()))
    bar.close()
    assert closed == [QAbstractAnimation.Stopped]
    QTest.qWait(250)
    assert second.y() == isolated.y()
    second.close()
    isolated.close()
    QTest.qWait(30)

    bars = [RoundProgressToast.new(position=position, parent=owners[0])
            for position in ToastPosition]
    QTest.qWait(250)
    owners[0].resize(1200, 900)
    QTest.qWait(50)
    for item in bars:
        assert item.pos() == item.manager.slideEndPos(item)
        item.close()
    auto = RoundProgressToast.info(duration=30, parent=owners[0])
    autoClosed = []
    auto.closed.connect(lambda: autoClosed.append(auto.progressRing.aniGroup.state()))
    QTest.qWait(60)
    assert autoClosed == [QAbstractAnimation.Stopped]
    for position in ToastPosition:
        assert not ToastManager.get(position).toastInfoBars
    for owner in owners:
        owner.close()
    print("PASS: capsule paint, accent changes, original animation, hide/resume, text, stacking, positions and close")


if __name__ == "__main__":
    run()
