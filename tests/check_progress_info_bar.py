"""Run with py -3.9 tests/check_progress_info_bar.py [preview.png]."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QAbstractAnimation, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import (
    IndeterminateProgressRing, InfoBar, InfoBarManager, InfoBarPosition,
    ProgressInfoBar, Theme, setTheme, setThemeColor, themeColor,
)


def run():
    app = QApplication([])
    owner = QWidget()
    owner.resize(1000, 800)
    owner.show()
    bar = ProgressInfoBar.new("请勿离开", "正在发送邮件，请耐心等待...", parent=owner)
    ring = bar.progressRing
    assert isinstance(ring, IndeterminateProgressRing)
    assert bar.duration == -1 and bar.isIndeterminate()
    assert ring.size().width() == 20 and ring.getStrokeWidth() == 3
    assert ring.aniGroup.loopCount() == -1
    assert ring.aniGroup.duration() == 2000
    assert ring.startAngleAni1.endValue() == 450
    assert ring.startAngleAni2.endValue() == 1080
    assert ring.spanAngleAni1.endValue() == 180
    QTest.qWait(250)
    assert ring.aniGroup.state() == QAbstractAnimation.Running
    assert ring.spanAngle > 0 and ring.startAngle > 0
    bar.hide()
    assert ring.aniGroup.state() == QAbstractAnimation.Paused
    time = ring.aniGroup.currentTime()
    QTest.qWait(40)
    assert ring.aniGroup.currentTime() == time
    bar.show()
    QTest.qWait(40)
    assert ring.aniGroup.state() == QAbstractAnimation.Running
    assert ring.aniGroup.currentTime() > time

    changes = []
    bar.valueChanged.connect(changes.append)
    bar.setValue(65)
    assert changes == [65] and bar.value() == 65
    assert not bar.isIndeterminate() and bar.determinateRing.isVisible()
    assert ring.aniGroup.state() == QAbstractAnimation.Stopped
    assert bar.determinateRing.val == 65
    bar.setValue(200)
    assert bar.value() == 100 and bar.isVisible()
    bar.setValue(-10)
    assert bar.value() == 0
    bar.setIndeterminate(True)
    assert ring.aniGroup.state() == QAbstractAnimation.Running

    manager = InfoBarManager.make(bar.position)
    oldWidth = bar.width()
    bar.setRemainingTime("剩余 10 秒")
    assert bar.remainingTime() == "剩余 10 秒"
    assert "剩余 10 秒" in bar.contentLabel.text()
    assert bar.width() > oldWidth
    assert bar.pos() == manager._pos(bar)
    bar.setContent("正在上传附件...")
    assert bar.content == "正在上传附件... · 剩余 10 秒"
    bar.setRemainingTime("")
    assert bar.content == "正在上传附件..."
    bar.setTitle("")
    bar.setContent("")
    assert bar.titleLabel.isHidden() and bar.contentLabel.isHidden()
    bar.setTitle("请勿离开")
    bar.setContent("正在发送邮件，请耐心等待...")
    assert not bar.titleLabel.isHidden() and not bar.contentLabel.isHidden()

    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        setThemeColor(QColor("#009faa"))
        QTest.qWait(40)
        assert ring.lightBarColor() == themeColor()
        assert ring.darkBarColor() == themeColor()
        assert bar.determinateRing.barColor() == themeColor()
        # Compare the unadorned background to an ordinary neutral InfoBar.
        plain = InfoBar.info("Title", "Content", position=InfoBarPosition.NONE, parent=owner)
        plain.setGraphicsEffect(None)
        bar.setGraphicsEffect(None)
        QTest.qWait(20)
        a, b = bar.grab().toImage(), plain.grab().toImage()
        assert a.pixelColor(round(3 * a.devicePixelRatio()), round(20 * a.devicePixelRatio())) == b.pixelColor(round(3 * b.devicePixelRatio()), round(20 * b.devicePixelRatio()))
        plain.close()
    bar.setCustomBarColor("#112233", "#445566")
    assert ring.lightBarColor().name() == "#112233"
    assert bar.determinateRing.darkBarColor().name() == "#445566"

    second = ProgressInfoBar.new("Another task", "Waiting", parent=owner)
    QTest.qWait(250)
    oldY = second.y()
    bar.setContent("First line\nSecond line\nThird line")
    assert second.y() > oldY and second.pos() == manager._pos(second)
    closed = []
    bar.closedSignal.connect(lambda: closed.append(True))
    bar.closeButton.click()
    assert closed == [True] and ring.aniGroup.state() == QAbstractAnimation.Stopped
    QTest.qWait(250)
    assert second.y() == manager.margin
    second.close()
    QTest.qWait(30)

    bars = []
    for position in InfoBarPosition:
        item = ProgressInfoBar.new("Task", "Working...", position=position, parent=owner)
        bars.append(item)
    QTest.qWait(250)
    for item in bars:
        if item.position != InfoBarPosition.NONE:
            assert item.pos() == InfoBarManager.make(item.position)._pos(item)
    owner.resize(1200, 900)
    QTest.qWait(50)
    for item in bars:
        if item.position != InfoBarPosition.NONE:
            assert item.pos() == InfoBarManager.make(item.position)._pos(item)
        item.close()
    QTest.qWait(30)

    vertical = ProgressInfoBar.info("Task", "Description", orient=Qt.Vertical,
                                    isClosable=False, position=InfoBarPosition.NONE,
                                    parent=owner)
    assert isinstance(vertical, ProgressInfoBar) and vertical.closeButton.isHidden()
    vertical.close()
    for factory in (ProgressInfoBar.success, ProgressInfoBar.warning, ProgressInfoBar.error):
        status = factory("Task status", "Completed", duration=-1,
                         position=InfoBarPosition.NONE, parent=owner)
        assert isinstance(status, InfoBar) and not isinstance(status, ProgressInfoBar)
        status.close()
    auto = ProgressInfoBar.new("Temporary", "Closing soon", duration=30,
                               position=InfoBarPosition.NONE, parent=owner)
    stopped = []
    auto.closedSignal.connect(lambda: stopped.append(auto.progressRing.aniGroup.state()))
    QTest.qWait(300)
    assert stopped == [QAbstractAnimation.Stopped]
    if len(sys.argv) > 1:
        setTheme(Theme.LIGHT)
        preview = ProgressInfoBar.new("请勿离开", "正在发送邮件，请耐心等待...",
                                      position=InfoBarPosition.NONE, parent=owner)
        QTest.qWait(500)
        preview.grab().save(sys.argv[1])
        print("Preview logical size:", preview.width(), preview.height())
        preview.close()
    owner.close()
    print("PASS: shared animation, visibility lifecycle, values, text/ETA updates, themes, stacking, positions and resize")


if __name__ == "__main__":
    run()
