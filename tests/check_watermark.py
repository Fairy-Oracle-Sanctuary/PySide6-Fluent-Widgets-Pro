"""Watermark rendering, target lifecycle, input pass-through and cache checks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton, QScrollArea, QWidget
from shiboken6 import isValid

from qfluentwidgets_pro import Theme, Watermark, setTheme


def run():
    app = QApplication([])
    owner = QWidget()
    owner.resize(700, 520)
    target = QWidget(owner)
    target.setGeometry(20, 20, 640, 360)
    target.setStyleSheet('background: #204060;')
    button = QPushButton('Click through', target)
    button.setGeometry(25, 25, 180, 40)
    edit = QLineEdit(target)
    edit.setGeometry(25, 85, 240, 40)
    owner.show()
    assert QTest.qWaitForWindowExposed(owner)
    owner.raise_()
    owner.activateWindow()
    QTest.qWait(100)
    watermark = Watermark('QFluentWidgets', target)
    QTest.qWait(20)
    assert watermark.targetWidget() is target and watermark.geometry() == target.rect()
    assert watermark.testAttribute(Qt.WA_TransparentForMouseEvents)
    assert watermark.testAttribute(Qt.WA_NoSystemBackground)
    assert watermark.focusPolicy() == Qt.NoFocus
    assert not watermark.autoFillBackground()
    assert watermark.text() == 'QFluentWidgets' and watermark.opacity() == .1
    assert watermark.angle() == -15 and watermark.spacing().width() == 60
    clicks = []
    button.clicked.connect(lambda: clicks.append(True))
    # Use Qt's child hit test, independent of other desktop windows covering us.
    hit = owner.childAt(button.mapTo(owner, button.rect().center()))
    assert hit is button, type(hit)
    QTest.mouseClick(hit, Qt.LeftButton)
    assert clicks == [True]
    hit = owner.childAt(edit.mapTo(owner, edit.rect().center()))
    assert hit is edit
    QTest.mouseClick(hit, Qt.LeftButton)
    QTest.keyClicks(edit, 'Editable below watermark')
    assert edit.text() == 'Editable below watermark' and edit.hasFocus()
    edit.clearFocus()  # Keep the blinking caret out of pixel comparisons.
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        QTest.qWait(20)
        watermark.hide()
        baseline = target.grab().toImage()
        watermark.show()
        watermark.setOpacity(.5)
        withWatermark = target.grab().toImage()
        assert withWatermark != baseline
        assert watermark.color().name() == ('#ffffff' if theme == Theme.DARK else '#000000')
        tile = watermark._tile
        assert tile is not None and tile.devicePixelRatio() == watermark.devicePixelRatioF()
        target.grab()
        assert watermark._tile is tile  # Do not regenerate on every paint/resize.
        target.resize(620, 380)
        QTest.qWait(10)
        assert watermark.geometry() == target.rect()
        target.grab()
        assert watermark._tile is tile
        watermark.hide()
        resizedBaseline = target.grab().toImage()
        watermark.show()
        watermark.setOpacity(0)
        assert target.grab().toImage() == resizedBaseline
        watermark.setOpacity(.5)
        watermark.setText('')
        assert target.grab().toImage() == resizedBaseline
        watermark.setText('QFluentWidgets')
    watermark.setText('<b>Literal text</b>\nSecond line 中文')
    assert watermark.text() == '<b>Literal text</b>\nSecond line 中文'
    target.grab()
    originalTile = watermark._tile
    watermark.setAngle(30)
    assert watermark._tile is None and watermark.angle() == 30
    target.grab()
    assert watermark._tile is not originalTile
    watermark.setSpacing(10, 20)
    assert watermark.spacing().width() == 10 and watermark.spacing().height() == 20
    returned = watermark.spacing()
    returned.setWidth(99)
    assert watermark.spacing().width() == 10
    font = QFont(watermark.font())
    font.setPixelSize(24)
    target.grab()
    watermark.setFont(font)
    assert watermark._tile is None
    watermark.setColor('#123456', '#abcdef')
    assert watermark.color().name() == '#abcdef'
    returned = watermark.color()
    returned.setRed(0)
    assert watermark.color().name() == '#abcdef'
    watermark.setColor('red')
    assert watermark.color().name() == '#ff0000'
    watermark.setSpacing(30)
    assert watermark.spacing().height() == 30
    for call in (lambda: watermark.setOpacity(-.1), lambda: watermark.setOpacity(1.1),
                 lambda: watermark.setOpacity(float('nan')), lambda: watermark.setAngle(float('inf')),
                 lambda: watermark.setSpacing(-1, 20), lambda: watermark.setSpacing(20, float('nan')),
                 lambda: watermark.setColor('invalid'), lambda: watermark.setTargetWidget(watermark),
                 lambda: watermark.setTargetWidget(QWidget(watermark))):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid watermark setting accepted')
    # Newly inserted or explicitly raised content must not cover the overlay.
    cover = QWidget(target)
    cover.setGeometry(target.rect())
    cover.setStyleSheet('background: #800000;')
    cover.show()
    cover.raise_()
    QTest.qWait(20)
    assert target.findChildren(QWidget, options=Qt.FindDirectChildrenOnly)[-1] is watermark
    cover.lower()
    cover.raise_()
    QTest.qWait(20)
    assert target.findChildren(QWidget, options=Qt.FindDirectChildrenOnly)[-1] is watermark
    assert owner.childAt(cover.mapTo(owner, QPoint(10, 10))) is cover
    cover.setParent(None)
    cover.close()
    target.hide()
    assert not watermark.isVisible()
    target.show()
    QTest.qWait(20)
    assert watermark.isVisible()
    other = QWidget(owner)
    other.setGeometry(20, 420, 640, 80)
    other.show()
    watermark.hide()
    watermark.setTargetWidget(other)
    assert watermark.targetWidget() is other and watermark.geometry() == other.rect()
    assert watermark.isHidden()
    watermark.show()
    oldGeometry = watermark.geometry()
    target.resize(400, 250)
    QTest.qWait(10)
    assert watermark.geometry() == oldGeometry  # Previous target no longer drives it.
    watermark.setTargetWidget(None)
    assert watermark.targetWidget() is None and watermark.parentWidget() is None and watermark.isHidden()
    scroll = QScrollArea(owner)
    scroll.resize(300, 200)
    content = QWidget()
    content.resize(1000, 800)
    scroll.setWidget(content)
    scroll.show()
    watermark.setTargetWidget(scroll.viewport())
    QTest.qWait(20)
    geometry = watermark.geometry()
    scroll.verticalScrollBar().setValue(200)
    scroll.horizontalScrollBar().setValue(200)
    assert watermark.geometry() == geometry and watermark.parentWidget() is scroll.viewport()
    # Parent ownership cleans up both the overlay and its pending sync timer.
    doomed = QWidget()
    attached = Watermark('Owned by target', doomed)
    doomed.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    assert not isValid(attached)
    from gallery_fixtures.watermark_demo import WatermarkDemo
    demo = WatermarkDemo()
    demo.resize(900, 950)
    demo.show()
    QTest.qWait(30)
    demo.textEdit.setText('Caller supplied 文本')
    assert all(w.text() == 'Caller supplied 文本' for w in demo.watermarks)
    demo.visibleCheckBox.setChecked(False)
    assert all(w.isHidden() for w in demo.watermarks)
    demo.visibleCheckBox.setChecked(True)
    demo.opacityBox.setValue(.24)
    demo.angleBox.setValue(-30)
    assert all(w.opacity() == .24 and w.angle() == -30 for w in demo.watermarks)
    demo.clickButton.click()
    assert demo._clicks == 1
    demo.close()
    watermark.close()
    owner.close()
    print('PASS: tiled native watermark, DPI/cache, themes, literal text, opacity, colors/font/spacing, '
          'input pass-through, resize/z-order, retarget/detach, scrolling, ownership and demo controls')


if __name__ == '__main__':
    run()
