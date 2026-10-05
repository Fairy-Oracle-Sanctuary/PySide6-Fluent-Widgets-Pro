"""Run with py -3.9 tests/check_toast.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import Toast, ToastPosition, ToastManager, Theme, setTheme


def run():
    app = QApplication([])
    owners = [QWidget(), QWidget()]
    for owner in owners:
        owner.resize(900, 700)
        owner.show()
    bars = []
    for position in ToastPosition:
        bar = Toast.success('Lesson 4', 'With respect, let us advance.',
                            duration=-1, position=position, parent=owners[0])
        bars.append(bar)
    assert len({id(bar.manager) for bar in bars}) == 6
    QTest.qWait(250)
    for bar in bars:
        assert bar.pos() == bar.manager.slideEndPos(bar)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        QTest.qWait(30)
        bar = bars[0]
        bar.setGraphicsEffect(None)
        image = bar.grab().toImage()
        scale = image.devicePixelRatio()
        accent = image.pixelColor(round(bar.width() / 2 * scale), round(2 * scale))
        assert accent == bar.toastColor
        body = image.pixelColor(round(10 * scale), round(20 * scale))
        assert body.name() == ('#f2f2f2' if theme == Theme.LIGHT else '#323232')
    duplicate = Toast.success('Other window', 'Independent stack', duration=-1, parent=owners[1])
    assert duplicate.manager.slideEndPos(duplicate).y() == bars[3].manager.margin + round(bars[3].manager.margin / 2.5)
    first = bars[3]
    second = Toast.info('Next', 'Stacked notification', duration=-1, parent=owners[0])
    assert second.manager.slideEndPos(second).y() > first.manager.slideEndPos(first).y()
    first.close()
    QTest.qWait(250)
    assert second.pos().y() == duplicate.pos().y()
    auto = Toast.warning('Auto close', 'Short duration', duration=30, parent=owners[0])
    closed = []
    auto.closed.connect(lambda: closed.append(True))
    QTest.qWait(80)
    assert closed == [True]
    for bar in bars:
        if bar is not first:
            bar.close()
    duplicate.close()
    second.close()
    QTest.qWait(50)
    for position in ToastPosition:
        assert not ToastManager.get(position).toastInfoBars
    for owner in owners:
        owner.close()
    print('PASS: themes, accent/body paint, six positions, window isolation, stacking and auto-close')


if __name__ == '__main__':
    run()
