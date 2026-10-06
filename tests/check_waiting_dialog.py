"""Waiting dialog geometry, Esc, reuse and animation lifecycle; owned UI only."""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QAbstractAnimation, QLocale, QPoint, QSize, Qt
from PySide6.QtGui import QImage, QKeySequence, QShortcut
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QPushButton, QWidget

from qfluentwidgets_pro import FluentTranslator, IndeterminateProgressRing, Theme, WaitingDialog, setTheme, setThemeColor, themeColor


def run():
    app = QApplication([])
    window = QWidget()
    window.resize(960, 770)
    window.move(40, 40)
    child = QWidget(window)
    dialog = WaitingDialog('请耐心等待...', '正在准备下载任务中 ...', child)
    window.show()
    window.activateWindow()
    QTest.qWait(80)
    assert dialog.parentWidget() is window
    assert isinstance(dialog.progressRing, IndeterminateProgressRing)
    assert dialog.progressRing.aniGroup.state() == QAbstractAnimation.Stopped
    assert not dialog.findChildren(QPushButton)
    assert dialog.isModal() and not dialog.isClosableOnMaskClicked()
    assert dialog.title() == '请耐心等待...'
    assert dialog.content() == '正在准备下载任务中 ...'
    rejected, accepted, finished, shortcuts = [], [], [], []
    dialog.rejected.connect(lambda: rejected.append(True))
    dialog.accepted.connect(lambda: accepted.append(True))
    dialog.finished.connect(finished.append)
    registered = QShortcut(QKeySequence('Esc'), window)
    registered.setContext(Qt.ApplicationShortcut)
    registered.activated.connect(lambda: shortcuts.append(True))

    def openDialog(wait=240):
        dialog.open()
        QTest.qWait(wait)
        assert dialog.isVisible() and dialog._filterInstalled
        assert dialog.progressRing.aniGroup.state() == QAbstractAnimation.Running
        assert dialog.size() == window.size()
        assert dialog.pos() == window.mapToGlobal(QPoint())
        assert abs(dialog.widget.geometry().center().x() - dialog.rect().center().x()) <= 1
        assert abs(dialog.widget.geometry().center().y() - dialog.rect().center().y()) <= 1
        if app.platformName() == 'windows' and dialog.title() == '请耐心等待...':
            assert dialog.widget.size() == QSize(300, 132), dialog.widget.size()

    def assertClosed(result):
        QTest.qWait(170)
        assert not dialog.isVisible() and not dialog._filterInstalled
        assert dialog.progressRing.aniGroup.state() == QAbstractAnimation.Stopped
        assert dialog.graphicsEffect() is None
        assert dialog.result() == result

    openDialog()
    oldAngle = dialog.progressRing.startAngle
    QTest.qWait(120)
    assert dialog.progressRing.startAngle != oldAngle
    QTest.mouseClick(dialog.windowMask, Qt.LeftButton, pos=QPoint(20, 20))
    assert dialog.isVisible() and not rejected
    QTest.keyClick(dialog.contentLabel, Qt.Key_Escape)
    assert dialog.progressRing.aniGroup.state() == QAbstractAnimation.Stopped
    assertClosed(QDialog.Rejected)
    assert len(rejected) == 1 and not accepted and not shortcuts
    openDialog(wait=10)  # Esc before fade-in completes.
    QTest.keyClick(dialog, Qt.Key_Escape)
    dialog.reject()  # Duplicate close requests emit only one result.
    assertClosed(QDialog.Rejected)
    assert len(rejected) == 2
    QTest.qWait(120)  # Old fade-in must not resurrect/reset a later dialog.
    openDialog()
    dialog.accept()
    assertClosed(QDialog.Accepted)
    assert len(accepted) == 1 and len(finished) == 3
    openDialog()
    QTest.keyClick(dialog, Qt.Key_Return)
    QTest.keyClick(dialog, Qt.Key_Space)
    assert dialog.isVisible()
    dialog.close()
    assertClosed(QDialog.Rejected)
    window.resize(820, 640)
    openDialog()
    window.resize(900, 680)
    app.processEvents()
    assert dialog.size() == window.size()
    window.move(80, 70)
    app.processEvents()
    assert dialog.pos() == window.mapToGlobal(QPoint())
    dialog.setTitle('正在处理')
    dialog.setContent('已准备好，请继续等待。')
    assert dialog.title() == '正在处理' and dialog.content() == '已准备好，请继续等待。'
    dialog.setContent('')
    assert dialog.contentLabel.isHidden()
    dialog.setTitle('请耐心等待...')
    dialog.setContent('正在准备下载任务中 ...')
    setThemeColor('#19BCD3')
    assert dialog.progressRing.lightBarColor().rgba() == themeColor().rgba()
    paths = []
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        assert dialog.progressRing.darkBarColor().rgba() == themeColor().rgba()
        for scale in (1, 2):
            raster = QImage(round(dialog.widget.width() * scale), round(dialog.widget.height() * scale),
                            QImage.Format_ARGB32_Premultiplied)
            raster.setDevicePixelRatio(scale)
            raster.fill(Qt.transparent)
            dialog.widget.render(raster, QPoint())
            assert not raster.isNull()
        QTest.qWait(220)
        path = str(Path(tempfile.gettempdir()) / ('codex-waiting-dialog-' + theme.value + '.png'))
        assert dialog.widget.grab().save(path)
        paths.append(path)
    window.hide()
    assertClosed(QDialog.Rejected)
    window.show()
    window.activateWindow()
    QTest.qWait(80)
    # A long status grows vertically without widening the reference panel.
    dialog.setTitle('Long task title that wraps across multiple lines')
    dialog.setContent('Preparing a longer task description. ' * 4)
    openDialog()
    assert dialog.widget.width() == 300 and dialog.widget.height() > 132
    dialog.hide()
    assert not dialog._filterInstalled and dialog.progressRing.aniGroup.state() == QAbstractAnimation.Stopped
    dialog.setTitle('Wait')
    dialog.setContent('Task')
    window.resize(240, 320)
    openDialog()
    assert dialog.widget.width() <= window.width() - 24
    assert dialog.widget.height() <= window.height() - 24
    assert dialog.progressRing.size() == QSize(40, 40)
    dialog.reject()
    assertClosed(QDialog.Rejected)
    window.resize(960, 770)
    dialog.setTitle('Wait')
    dialog.setContent('Task')
    openDialog()
    QTest.keyClick(dialog, Qt.Key_Escape)
    assertClosed(QDialog.Rejected)
    window.activateWindow()
    window.setFocus()
    QTest.qWait(80)
    QTest.keyClick(window, Qt.Key_Escape)
    assert shortcuts, 'App shortcuts must work again after the waiting dialog closes'
    translator = FluentTranslator(QLocale('zh_CN'))
    app.installTranslator(translator)
    localized = WaitingDialog(parent=window)
    assert localized.title() == '请耐心等待...'
    localized.deleteLater()
    app.removeTranslator(translator)
    try:
        WaitingDialog()
    except ValueError:
        pass
    else:
        raise AssertionError('A missing owner window should be reported clearly')
    dialog.deleteLater()
    window.close()
    app.processEvents()
    print('PASS: WaitingDialog geometry, real ring, Esc/early Esc, accept/reject/close/reuse, theme, parent tracking, shortcuts and DPI')
    print('Previews:', paths)


if __name__ == '__main__':
    run()
