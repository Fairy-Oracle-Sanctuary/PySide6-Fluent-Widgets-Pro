"""Native drawer geometry, transitions, shadow, dismissal and ownership tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QRect, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QLineEdit, QPushButton, QWidget
from shiboken6 import isValid

from qfluentwidgets_pro import Drawer, DrawerPosition, Theme, setTheme


def expected(position, width, height, size):
    if position == DrawerPosition.LEFT:
        return QRect(0, 0, min(size, width), height)
    if position == DrawerPosition.RIGHT:
        return QRect(max(0, width-size), 0, min(size, width), height)
    if position == DrawerPosition.TOP:
        return QRect(0, 0, width, min(size, height))
    return QRect(0, max(0, height-size), width, min(size, height))


def run():
    app = QApplication([])
    owner = QWidget()
    owner.setObjectName('drawerTestOwner')
    owner.resize(760, 520)
    owner.setStyleSheet('QWidget#drawerTestOwner { background: #808080; }')
    behind = QLineEdit(owner)
    behind.setGeometry(20, 20, 200, 40)
    owner.show()
    assert QTest.qWaitForWindowExposed(owner)
    owner.activateWindow()
    QTest.qWait(80)
    behind.setFocus()
    drawer = Drawer('Caller title', owner)
    inside = QLineEdit()
    button = QPushButton('Custom action')
    drawer.addWidget(inside)
    drawer.addWidget(button)
    drawer.viewLayout.addStretch()
    assert drawer.isHidden() and not drawer.isWindow() and not drawer.isOpen()
    assert isinstance(drawer.panel.graphicsEffect(), QGraphicsDropShadowEffect)
    assert drawer.shadowEffect.blurRadius() == 48 and drawer.shadowEffect.color().alpha() > 0
    assert drawer.closeButton.toolTip() == drawer.closeButton.accessibleName() == 'Close'
    assert drawer.title() == 'Caller title'
    opened, closed = [], []
    drawer.opened.connect(lambda: opened.append(True))
    drawer.closed.connect(lambda: closed.append(True))
    drawer.setAnimationDuration(0)
    for position in DrawerPosition:
        behind.setFocus()
        drawer.open(position)
        QTest.qWait(10)
        assert drawer.isVisible() and drawer.isOpen()
        assert drawer.geometry() == owner.rect()
        assert drawer.panel.geometry() == expected(position, 760, 520, 320)
        count = len(opened)
        drawer.open()
        assert len(opened) == count
        inside.setFocus()
        QTest.keyClicks(inside, 'Native')
        assert inside.text().endswith('Native')
        for _ in range(8):
            QTest.keyClick(QApplication.focusWidget(), Qt.Key_Tab)
            assert drawer.isAncestorOf(QApplication.focusWidget())
        owner.resize(900, 600)
        QTest.qWait(10)
        assert drawer.geometry() == owner.rect()
        assert drawer.panel.geometry() == expected(position, 900, 600, 320)
        drawer.setDrawerSize(2000)
        assert drawer.panel.geometry() == owner.rect()
        drawer.setDrawerSize(320)
        drawer.closeButton.click()
        assert drawer.isHidden() and not drawer.isOpen() and behind.hasFocus()
        owner.resize(760, 520)
        QTest.qWait(10)
    assert len(opened) == len(closed) == 4
    drawer.open('right')
    # Mask consumes the press instead of invoking the underlying input/control.
    assert owner.childAt(behind.mapTo(owner, behind.rect().center())) is drawer
    drawer.setClosableOnMaskClicked(False)
    QTest.mouseClick(drawer, Qt.LeftButton, pos=QPoint(10, 300))
    assert drawer.isOpen()
    drawer.setEscClosable(False)
    inside.setFocus()
    QTest.keyClick(inside, Qt.Key_Escape)
    assert drawer.isOpen()
    drawer.setEscClosable(True)
    QTest.keyClick(inside, Qt.Key_Escape)
    assert drawer.isHidden()
    drawer.open()
    drawer.setClosableOnMaskClicked(True)
    QTest.mouseClick(drawer, Qt.LeftButton, pos=QPoint(10, 300))
    assert drawer.isHidden()
    drawer.setTitle('<b>Plain caller title</b>')
    assert drawer.titleLabel.textFormat() == Qt.PlainText
    drawer.setMaskColor(QColor(10, 20, 30, 50))
    color = drawer.maskColor()
    color.setAlpha(0)
    assert drawer.maskColor().alpha() == 50
    drawer.setAnimationDuration(160)
    drawer.open()
    QTest.qWait(40)
    assert 0 < drawer._progress < 1
    progress = drawer._progress
    drawer.close()
    assert drawer._progress == progress and drawer.isVisible() and not drawer.isOpen()
    QTest.qWait(35)  # Allow at least two animation frames before inspecting progress.
    assert drawer._progress < progress
    progress = drawer._progress
    drawer.open(DrawerPosition.LEFT)
    assert drawer._progress == progress
    owner.resize(820, 580)
    QTest.qWait(220)
    assert drawer.panel.geometry() == expected(DrawerPosition.LEFT, 820, 580, 320)
    drawer.close()
    QTest.qWait(220)
    assert drawer.isHidden() and drawer._progress == 0
    drawer.show()
    QTest.qWait(200)
    drawer.hide()
    assert drawer.isHidden()
    drawer.setVisible(True)
    QTest.qWait(200)
    assert drawer.isOpen() and drawer._progress == 1
    drawer.setVisible(False)
    assert not drawer.isOpen() and drawer.isHidden()
    drawer.setAnimationDuration(0)
    drawer.open()
    owner.hide()
    assert drawer.isHidden() and not drawer.isOpen()
    owner.show()
    QTest.qWait(20)
    assert drawer.isHidden()  # Hidden parents must not unexpectedly reopen it.
    for theme in (Theme.DARK, Theme.LIGHT):
        setTheme(theme)
        drawer.open(DrawerPosition.RIGHT)
        QTest.qWait(30)
        image = owner.grab().toImage()
        dpr = image.devicePixelRatio()
        # Far from both text and shadow: panel is opaque; adjacent shadow is darker.
        panelColor = image.pixelColor(round(800*dpr), round(480*dpr))
        assert panelColor.name() == ('#202020' if theme == Theme.DARK else '#ffffff'), (theme, panelColor.name())
        edge = drawer.panel.x()
        near = image.pixelColor(round((edge-4)*dpr), round(480*dpr)).lightness()
        far = image.pixelColor(round((edge-70)*dpr), round(480*dpr)).lightness()
        assert near < far, 'Inward-facing edge must have a visible shadow'
        drawer.hide()
    for call in (lambda: Drawer(), lambda: drawer.setDrawerSize(0),
                 lambda: drawer.setAnimationDuration(-1), lambda: drawer.setPosition('invalid'),
                 lambda: drawer.setMaskColor('invalid'), lambda: drawer.addWidget(drawer)):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid drawer setting accepted')
    doomed = QWidget()
    attached = Drawer(parent=doomed)
    doomed.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    assert not isValid(attached)
    from gallery_fixtures.drawer_demo import DrawerDemo
    demo = DrawerDemo()
    demo.resize(900, 820)
    demo.show()
    QTest.qWait(20)
    demo.animateCheckBox.setChecked(False)
    for position, trigger in demo.directionButtons.items():
        trigger.click()
        assert demo.drawer.isOpen() and demo.drawer.position() == position
        demo.drawer.close()
    demo.close()
    owner.close()
    print('PASS: four drawer edges, native shadow/themes, custom content, resize/clamping, animation reversal, '
          'close/Esc/mask, focus containment/restore, hide/show, parent ownership and demo controls')


if __name__ == '__main__':
    run()
