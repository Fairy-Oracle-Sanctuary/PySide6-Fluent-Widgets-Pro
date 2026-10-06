"""Timeline card interaction and rendering, using only owned Qt windows."""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from qfluentwidgets_pro import CardWidget, InfoBarIcon, Theme, TimeLineItem, TimeLineWidget, setTheme


def run():
    app = QApplication([])
    window = QWidget()
    window.resize(700, 650)
    layout = QVBoxLayout(window)
    timeline = TimeLineWidget(window)
    layout.addWidget(timeline, 0, Qt.AlignLeft)
    layout.addStretch()
    completed = timeline.addGroup('已完成', InfoBarIcon.SUCCESS)
    item = completed.addItem('<s>全军出击，誓死保卫鸽鸽！！</s>', InfoBarIcon.SUCCESS)
    today = timeline.addGroup('今日安排')
    today.addItem('上传我家 aiko 的 MV『シアワセ』', InfoBarIcon.WARNING)
    today.addItem('下载我家 aiko 的『荒れた唇は恋を失くす』', InfoBarIcon.WARNING)
    pending = timeline.addGroup('待办事项', InfoBarIcon.ERROR)
    pending.addItem('单曲循环我家 aiko 的新歌『星の降る日に』', InfoBarIcon.ERROR)
    window.show()
    window.activateWindow()
    QTest.qWait(80)
    assert isinstance(item, CardWidget) and isinstance(item, TimeLineItem)
    assert item.isClickEnabled() and item.borderRadius == 10 and item.minimumHeight() == 50
    assert timeline.maximumWidth() == 370 and timeline.width() == 370
    assert item.width() == 328 and item.height() == 50
    assert timeline.height() == 408
    assert today.y() - completed.y() == 115
    assert pending.y() - today.y() == 184
    assert today.items[1].y() - today.items[0].y() == 69
    assert item.mapTo(timeline, QPoint()).x() == 42
    assert item.textLabel.x() == 40
    assert completed.titleLabel.x() == 40 and completed.titleLabel.font().bold()
    assert item.textLabel.wordWrap() and '<s>' in item.textLabel.text()
    assert item.layout().contentsMargins().left() == 4
    assert item.layout().contentsMargins().top() == 7
    assert item.layout().spacing() == 0
    clicks = []
    item.clicked.connect(lambda: clicks.append(True))
    points = [QPoint(6, 6), item.iconWidget.mapTo(item, item.iconWidget.rect().center()),
              item.textLabel.mapTo(item, item.textLabel.rect().center())]
    for point in points:
        count = len(clicks)
        QTest.mouseClick(window.windowHandle(), Qt.LeftButton, pos=item.mapTo(window, point))
        app.processEvents()
        assert len(clicks) == count + 1, 'Every part of a card must emit exactly one click'
    count = len(clicks)
    QTest.mouseClick(item, Qt.RightButton)
    QTest.mouseRelease(item, Qt.LeftButton)
    QTest.mousePress(item, Qt.LeftButton, pos=QPoint(6, 6))
    assert item.isPressed
    QTest.mouseRelease(item, Qt.LeftButton, pos=QPoint(item.width() + 8, 6))
    assert not item.isPressed and len(clicks) == count
    item.setClickEnabled(False)
    QTest.mouseClick(item, Qt.LeftButton)
    QTest.keyClick(item, Qt.Key_Return)
    assert len(clicks) == count
    item.setClickEnabled(True)
    item.setEnabled(False)
    QTest.mouseClick(item, Qt.LeftButton)
    assert len(clicks) == count
    item.setEnabled(True)
    item.setFocus()
    for key in (Qt.Key_Return, Qt.Key_Space):
        QTest.keyClick(item, key)
    assert len(clicks) == count + 2
    item.setText('<b>更新后的事项</b>')
    assert item.textLabel.text() == '<b>更新后的事项</b>'
    item.setIcon(InfoBarIcon.ERROR)
    assert item.iconWidget.icon == InfoBarIcon.ERROR
    item.setIcon(InfoBarIcon.SUCCESS)
    item.setText('<s>全军出击，誓死保卫鸽鸽！！</s>')

    paths = []
    def move(widget, point):
        if app.platformName() == 'offscreen':
            QTest.mouseMove(window.windowHandle(), widget.mapTo(window, point))
        else:
            QTest.mouseMove(widget, point)

    for theme in (Theme.DARK, Theme.LIGHT):
        setTheme(theme)
        move(window, QPoint(window.width() - 5, window.height() - 5))
        QTest.qWait(180)
        assert item.backgroundColor.rgba() == item._normalBackgroundColor().rgba()
        normal = item.backgroundColor.rgba()
        move(item, QPoint(6, 6))
        QTest.qWait(180)
        assert item.isHover and item.backgroundColor.rgba() == item._hoverBackgroundColor().rgba()
        assert item.backgroundColor.rgba() != normal
        QTest.mousePress(item, Qt.LeftButton, pos=QPoint(6, 6))
        QTest.qWait(180)
        assert item.backgroundColor.rgba() == item._pressedBackgroundColor().rgba()
        QTest.mouseRelease(item, Qt.LeftButton, pos=QPoint(item.width() + 8, 6))
        move(window, QPoint(window.width() - 5, window.height() - 5))
        QTest.qWait(180)
        for scale in (1, 2):
            raster = QImage(round(timeline.width() * scale), round(timeline.height() * scale),
                            QImage.Format_ARGB32_Premultiplied)
            raster.setDevicePixelRatio(scale)
            raster.fill(Qt.transparent)
            timeline.render(raster, QPoint())
            assert not raster.isNull()
        path = str(Path(tempfile.gettempdir()) / ('codex-timeline-card-' + theme.value + '.png'))
        assert timeline.grab().save(path)
        paths.append(path)
    longItem = today.addItem('A long wrapping timeline item ' * 30)
    app.processEvents()
    assert longItem.textLabel.hasHeightForWidth()
    assert longItem.height() > 50 and longItem.width() == 328
    timeline.setFixedWidth(300)
    app.processEvents()
    assert item.width() == 258 and longItem.width() == 258
    today.removeItem(longItem)
    app.processEvents()
    assert longItem not in today.items
    completed.removeItem(item)
    assert not completed.items and completed.cards.isHidden()
    timeline.removeGroup(pending)
    assert pending not in timeline.groups
    timeline.clear()
    assert not timeline.groups
    window.close()
    app.processEvents()
    print('PASS: timeline CardWidget, whole-card clicks, hover/press, keyboard, disabled/drag cancellation, rich text, remove/clear and 1x/2x rendering')
    print('Previews:', paths)


if __name__ == '__main__':
    run()
