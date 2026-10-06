"""Toolbox arrow-only hover, height animation and interrupted exclusive transitions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QAbstractAnimation, QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QVBoxLayout, QWidget
from qfluentwidgets_pro import Theme, ToolBox, setTheme


def run():
    app = QApplication([])
    owner = QWidget()
    owner.setObjectName('animatedToolBoxOwner')
    owner.setStyleSheet('QWidget#animatedToolBoxOwner { background: #262626; }')
    owner.resize(520, 700)
    layout = QVBoxLayout(owner)
    box = ToolBox(owner)
    layout.addWidget(box)
    layout.addStretch()
    for title in ('Blend', 'Hue', 'Sharpen'):
        page = QWidget()
        content = QVBoxLayout(page)
        content.setContentsMargins(0, 0, 0, 0)
        label = QLabel('A native tool panel with a long description that wraps when the toolbox becomes narrower.')
        label.setWordWrap(True)
        content.addWidget(label)
        content.addWidget(QLineEdit('Persistent value'))
        box.addItem(page, title)
    owner.show()
    assert QTest.qWaitForWindowExposed(owner)
    owner.activateWindow()
    QTest.qWait(80)
    assert box.animationDuration() == 200

    def pump(duration):
        for _ in range(duration // 10):
            QTest.qWait(10)
            assert sum(item._extent > .5 for item in box._items) <= 1
            assert sum(item.body.isVisible() for item in box._items) <= 1
            assert [i for i, item in enumerate(box._items) if item.header.isChecked()] == (
                [] if box.currentIndex() < 0 else [box.currentIndex()])

    box.setCurrentIndex(-1)
    closing = box._items[0]
    initial = closing._extent
    assert initial > 0 and closing._animation.state() == QAbstractAnimation.Running
    pump(60)
    assert 0 < closing._extent < initial
    pump(180)
    assert closing.height() == 50 and closing.body.isHidden()
    box.setCurrentIndex(0)
    assert closing._extent == 0
    pump(60)
    assert 0 < closing._extent < closing._naturalExtent()
    # Content stays at its natural size; the viewport reveals it rather than squashing controls.
    assert closing.body.height() == closing._naturalExtent() - 1
    pump(180)
    assert closing.height() == 50 + closing._naturalExtent()
    assert box.widget(0).findChild(QLineEdit).text() == 'Persistent value'
    box.setCurrentIndex(1)
    assert not box._items[1].body.isVisible()
    pump(60)
    assert closing._extent > 0 and box._items[1]._extent == 0
    box.setCurrentIndex(2)  # Replace the pending destination while old page closes.
    pump(180)
    assert box._items[1]._extent == 0 and box._items[2]._extent > 0
    pump(220)
    assert box._items[2].height() == 50 + box._items[2]._naturalExtent()
    box.setCurrentIndex(-1)
    pump(60)
    extent = box._items[2]._extent
    box.setCurrentIndex(2)  # Reverse collapse smoothly, without resetting to zero.
    assert box._items[2]._extent == extent
    pump(240)
    box.setCurrentIndex(0)
    pump(250)
    owner.resize(330, 700)  # Retarget natural wrapped height during expansion.
    pump(240)
    assert box._items[0].height() == 50 + box._items[0]._naturalExtent()
    extra = QLabel('Dynamically inserted custom control')
    box.widget(0).layout().addWidget(extra)
    pump(40)
    assert box._items[0].height() == 50 + box._items[0]._naturalExtent()
    box.setCurrentIndex(1)
    pump(60)
    removed = box.removeItem(0)  # Remove the still-closing page without a stale callback.
    assert removed.parentWidget() is None and removed.isHidden()
    removed.deleteLater()
    pump(240)
    assert box.currentIndex() == 0
    box.setCurrentIndex(1)
    pump(50)
    box.setAnimationDuration(0)  # Finish all pending transitions immediately.
    assert box._items[0]._extent == 0 and box._items[1]._extent == box._items[1]._naturalExtent()
    box.setCurrentIndex(-1)
    assert all(item.height() == 50 and item.body.isHidden() for item in box._items)
    for theme in (Theme.DARK, Theme.LIGHT):
        setTheme(theme)
        pump(160)
        header = box.itemHeader(0)
        header.clearFocus()
        QTest.mouseMove(owner, QPoint(owner.width()-2, owner.height()-2))
        QTest.qWait(20)
        normal = box._items[0].grab().toImage()
        dpr = normal.devicePixelRatio()
        point = header.arrowRect().topLeft() + QPoint(6, 6)
        QTest.mouseMove(header, header.arrowRect().center())
        QTest.qWait(20)
        assert header._arrowHovered
        hovered = box._items[0].grab().toImage()
        x, y = point.x()+header.x(), point.y()+header.y()
        assert hovered.pixelColor(round(x*dpr), round(y*dpr)) != normal.pixelColor(round(x*dpr), round(y*dpr))
        # No full-card hover fill or inset frame.
        for x, y in ((6, 6), (12, 40), (100, 6)):
            assert hovered.pixelColor(round(x*dpr), round(y*dpr)) == normal.pixelColor(round(x*dpr), round(y*dpr))
        QTest.mouseMove(header, QPoint(15, 24))
        QTest.qWait(20)
        assert header._arrowHovered  # Entire header is a hot area; only its arrow is painted.
        QTest.mouseClick(header, Qt.LeftButton, pos=QPoint(15, 24))
        assert box.currentIndex() == 0 and not header._keyboardFocus
        QTest.mouseClick(header, Qt.LeftButton, pos=QPoint(15, 24))
        assert box.currentIndex() == -1 and not header._keyboardFocus
    try:
        box.setAnimationDuration(-1)
    except ValueError:
        pass
    else:
        raise AssertionError('Negative duration accepted')
    owner.close()
    print('PASS: arrow-only hover/no mouse focus frame, smooth expand/collapse/reversal, '
          'sequential exclusivity, rapid switching, resize/content changes, removal and animation disable')


if __name__ == '__main__':
    run()
