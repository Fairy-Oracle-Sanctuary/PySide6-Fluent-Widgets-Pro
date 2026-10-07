"""Native toolbox exclusivity, page lifecycle, keyboard and dynamic layout."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PySide6.QtGui import QIcon
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget
from shiboken6 import isValid

from qfluentwidgets_pro import FluentIcon, SimpleCardWidget, Theme, ToolBox, setTheme


def page(text):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    edit = QLineEdit(text)
    layout.addWidget(edit)
    return widget, edit


def run():
    app = QApplication([])
    owner = QWidget()
    owner.resize(550, 650)
    owner.setObjectName('toolBoxTestOwner')
    owner.setStyleSheet('QWidget#toolBoxTestOwner { background: #808080; }')
    layout = QVBoxLayout(owner)
    box = ToolBox(owner)
    box.setAnimationDuration(0)  # Existing lifecycle assertions use settled geometry.
    layout.addWidget(box)
    layout.addStretch()
    changes = []
    box.currentChanged.connect(changes.append)
    assert box.count() == 0 and box.currentIndex() == -1 and box.currentWidget() is None
    pages = [page('Persistent ' + str(i)) for i in range(3)]
    for i, (widget, edit) in enumerate(pages):
        assert box.addItem(widget, '<b>Caller title</b>' if i == 0 else 'Tool ' + str(i)) == i
    assert changes == [0] and box.currentWidget() is pages[0][0]
    assert all(isinstance(item, SimpleCardWidget) for item in box._items)
    owner.show()
    assert QTest.qWaitForWindowExposed(owner)
    owner.activateWindow()
    QTest.qWait(80)

    def exclusive(index):
        assert box.currentIndex() == index
        assert [i for i, item in enumerate(box._items) if not item.body.isHidden()] == ([] if index < 0 else [index])
        assert [i for i, item in enumerate(box._items) if item.header.isChecked()] == ([] if index < 0 else [index])

    exclusive(0)
    box.currentChanged.connect(exclusive)  # Exclusivity holds even during signal delivery.
    for index in (1, 2, 0):
        QTest.mouseClick(box.itemHeader(index), Qt.LeftButton, pos=QPoint(12, 24))
        exclusive(index)
        assert pages[index][1].text() == 'Persistent ' + str(index)
    pages[0][1].setText('User value survives collapse')
    QTest.mouseClick(box.itemHeader(0), Qt.LeftButton)
    exclusive(-1)
    QTest.qWait(20)
    collapsedHeight = box.sizeHint().height()
    header = box.itemHeader(1)
    header.setFocus()
    QTest.keyClick(header, Qt.Key_Space)
    exclusive(1)
    QTest.keyClick(header, Qt.Key_Return)
    exclusive(-1)
    box.setCurrentIndex(0)
    QTest.qWait(20)
    assert box.sizeHint().height() > collapsedHeight
    assert pages[0][1].text() == 'User value survives collapse'
    before = len(changes)
    box.setCurrentIndex(0)
    assert len(changes) == before
    box.setItemEnabled(0, False)
    exclusive(1)
    box.setCurrentIndex(0)
    exclusive(1)
    QTest.mouseClick(box.itemHeader(0), Qt.LeftButton)
    exclusive(1)
    box.setItemEnabled(1, False)
    exclusive(2)
    box.setItemEnabled(2, False)
    exclusive(-1)
    for index in range(box.count()):
        box.setItemEnabled(index, True)
    exclusive(-1)
    box.setCurrentIndex(1)
    inserted, insertedEdit = page('Inserted')
    box.insertItem(0, inserted, 'Inserted', FluentIcon.SETTING)
    exclusive(2)
    assert box.currentWidget() is pages[1][0] and box.indexOf(pages[2][0]) == 3
    assert box.itemIcon(0) == FluentIcon.SETTING
    box.setItemIcon(0, QIcon())
    box.setItemIcon(0, None)
    assert box.itemIcon(0) is None
    box.setItemText(0, 'New title')
    assert box.itemText(0) == box.itemHeader(0).accessibleName() == 'New title'
    removed = box.removeItem(0)
    exclusive(1)
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    assert removed is inserted and isValid(removed) and removed.parentWidget() is None and removed.isHidden()
    removed.deleteLater()
    removed = box.removeItem(1)
    exclusive(1)
    assert box.currentWidget() is pages[2][0] and isValid(removed)
    removed.deleteLater()
    box.removeItem(1).deleteLater()
    exclusive(0)
    box.removeItem(0).deleteLater()
    exclusive(-1)
    assert box.count() == 0
    for callback, error in ((lambda: box.setCurrentIndex(3), IndexError),
                            (lambda: box.removeItem(0), IndexError),
                            (lambda: box.addItem(box, 'Cycle'), ValueError),
                            (lambda: box.addItem('invalid', 'Tool'), TypeError)):
        try:
            callback()
        except error:
            pass
        else:
            raise AssertionError('Invalid toolbox operation accepted')
    for theme in (Theme.DARK, Theme.LIGHT):
        setTheme(theme)
        child, edit = page('Theme test')
        box.addItem(child, 'Tool', FluentIcon.GLOBE)
        QTest.qWait(160)
        item = box._items[0]
        image = item.grab().toImage()
        assert not image.isNull()
        assert item.header.isVisible() and edit.isVisible()
        owner.resize(300, 600)
        QTest.qWait(20)
        assert child.width() <= item.width() and item.header.width() == item.width()-2
        item.setFixedWidth(240)
        QTest.qWait(10)
        assert child.width() <= 216
        box.removeItem(0).deleteLater()
    from gallery_fixtures.tool_box_demo import ToolBoxDemo
    demo = ToolBoxDemo()
    demo.toolBox.setAnimationDuration(0)
    demo.resize(900, 650)
    demo.show()
    QTest.qWait(50)
    demo.opacitySlider.setValue(75)
    demo.toolBox.setCurrentIndex(1)
    demo.hueSlider.setValue(35)
    demo.toolBox.setCurrentIndex(0)
    assert demo.opacitySlider.value() == 75 and demo.hueSlider.value() == 35
    demo.applyButton.click()
    assert '75%' in demo.status.text() or '75％' in demo.status.text()
    demo.resetButton.click()
    assert demo.opacitySlider.value() == 30
    assert demo.toolBox._items[0].header.height() == 48
    assert all(not item.body.isVisible() for item in demo.toolBox._items[1:])
    demo.close()
    owner.close()
    print('PASS: exclusive expansion/collapse, mouse/Space/Enter, signals, preserved controls, '
          'insert/remove ownership, enabled state, themes, dynamic height/width and demo')


if __name__ == '__main__':
    run()
