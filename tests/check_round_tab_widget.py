"""Owned-widget API, page lifecycle, signals, drag and theme rendering checks."""

import os
import sys
import tempfile
from math import ceil
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QMouseEvent, QPainter, QPen
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTabWidget, QWidget
from shiboken6 import isValid

from qfluentwidgets_pro import FluentIcon, RoundTabBar, RoundTabWidget, TabBar, TabWidget, Theme, setTheme
from gallery.view.round_tab_widget_demo import RoundTabWidgetDemo


def checkSync(tabs):
    assert tabs.count() == tabs.tabBar.count()
    assert tabs.currentIndex() == tabs.tabBar.currentIndex()
    for index in range(tabs.count()):
        assert tabs.widget(index).property('routeKey') == tabs.tabBar.tabItem(index).routeKey()


def run():
    app = QApplication([])
    ordinary = TabWidget()
    assert type(ordinary.tabBar) is TabBar and ordinary.vBoxLayout.spacing() == 1
    tabs = RoundTabWidget()
    assert isinstance(tabs, TabWidget) and isinstance(tabs.tabBar(), RoundTabBar)
    assert tabs.count() == 0 and tabs.currentIndex() == -1 and tabs.currentWidget() is None
    assert tabs.vBoxLayout.spacing() == 0
    changes, closed, added, clicked, doubled = [], [], [], [], []
    tabs.currentChanged.connect(changes.append)
    tabs.tabCloseRequested.connect(closed.append)
    tabs.tabAddRequested.connect(lambda: added.append(True))
    tabs.tabBarClicked.connect(clicked.append)
    tabs.tabBarDoubleClicked.connect(doubled.append)
    first, second, third = QWidget(), QWidget(), QWidget()
    assert tabs.addTab(first, 'First') == 0 and changes == [0]
    assert tabs.addTab(second, QIcon(), 'Second') == 1
    assert tabs.addTab(third, 'Third', FluentIcon.HOME, 'third') == 2
    assert tabs.addPage(QWidget(), 'Fourth', routeKey='fourth') == 3
    assert tabs.addTab(first, 'Duplicate') == -1
    try:
        tabs.addTab(QWidget(), 'Duplicate key', routeKey='third')
    except ValueError:
        pass
    else:
        raise AssertionError('duplicate route key accepted')
    assert tabs.indexOf(first) == 0 and tabs.indexOf(QWidget()) == -1 and tabs.indexOf(None) == -1
    tabs.setCurrentIndex(1)
    tabs.setCurrentWidget(third)
    tabs.setCurrentIndex(2)
    tabs.setCurrentIndex(99)
    tabs.setCurrentIndex(-1)
    assert changes == [0, 1, 2] and tabs.currentWidget() is third
    checkSync(tabs)
    inserted = QWidget()
    assert tabs.insertTab(0, inserted, QIcon(), 'Inserted') == 0
    assert tabs.currentWidget() is third and tabs.currentIndex() == 3 and changes[-1] == 2
    tabs.removeTab(0)
    assert isValid(inserted) and tabs.indexOf(inserted) == -1 and inserted.isHidden()
    assert tabs.currentWidget() is third and changes[-1] == 2
    checkSync(tabs)
    assert tabs.insertTab(99, inserted, 'Appended') == 4
    tabs.setTabText(1, 'Renamed')
    tabs.setTabIcon(1, FluentIcon.MUSIC)
    tabs.setTabToolTip(1, 'Tip')
    tabs.setTabWhatsThis(1, 'Help')
    tabs.setTabData(1, {'id': 42})
    assert tabs.tabText(1) == 'Renamed' and tabs.tabToolTip(1) == 'Tip'
    assert tabs.tabWhatsThis(1) == 'Help' and tabs.tabData(1) == {'id': 42}
    tabs.setTabVisible(0, False)
    assert not tabs.isTabVisible(0) and tabs.currentWidget() is third
    tabs.setTabVisible(2, False)
    assert tabs.currentIndex() == 3
    tabs.setTabVisible(0, True)
    tabs.setTabVisible(2, True)
    tabs.setCurrentWidget(third)
    tabs.setTabEnabled(2, False)
    assert not tabs.isTabEnabled(2) and not third.isEnabled() and tabs.currentIndex() == 3
    tabs.setTabEnabled(2, True)
    checkSync(tabs)
    tabs.resize(720, 400)
    tabs.show()
    tabs.activateWindow()
    QTest.qWait(100)
    tabs.setCurrentIndex(1)
    QTest.mouseClick(tabs.windowHandle(), Qt.LeftButton,
                     pos=tabs.tabBar.tabItem(2).mapTo(tabs, QPoint(45, 16)))
    assert tabs.currentWidget() is third and clicked == [2]
    QTest.mouseDClick(tabs.tabBar.tabItem(0), Qt.LeftButton, pos=QPoint(45, 16))
    assert doubled == [0]
    QTest.mouseClick(tabs.tabBar.tabItem(1).closeButton, Qt.LeftButton)
    assert closed == [1] and tabs.count() == 5
    QTest.mouseClick(tabs.tabBar.addButton, Qt.LeftButton)
    assert added == [True] and tabs.count() == 5
    tabs.setCurrentIndex(0)
    tabs.setTabEnabled(1, False)
    tabs._cycleTab(1)
    assert tabs.currentIndex() == 2
    tabs._cycleTab(-1)
    assert tabs.currentIndex() == 0
    tabs.setTabEnabled(1, True)
    QTest.keyClick(tabs, Qt.Key_Tab, Qt.ControlModifier)
    assert tabs.currentIndex() == 1
    QTest.keyClick(tabs, Qt.Key_Tab, Qt.ControlModifier | Qt.ShiftModifier)
    assert tabs.currentIndex() == 0

    # Drag changes the actual page order, not just the selected header.
    tabs.setMovable(True)
    firstItem = tabs.tabBar.tabItem(0)
    before = len(changes)
    QTest.mousePress(firstItem, Qt.LeftButton, pos=QPoint(50, 16))
    destination = QPoint(firstItem.width() + 60, 16)
    move = QMouseEvent(QEvent.MouseMove, QPointF(destination), QPointF(firstItem.mapToGlobal(destination)),
                       Qt.NoButton, Qt.LeftButton, Qt.NoModifier)
    app.sendEvent(firstItem, move)
    QTest.mouseRelease(firstItem, Qt.LeftButton, pos=QPoint(50, 16))
    QTest.qWait(300)
    assert tabs.widget(1) is first and tabs.currentWidget() is first and tabs.currentIndex() == 1
    assert changes[before:] == [1]
    checkSync(tabs)
    pages = [tabs.widget(index) for index in range(tabs.count())]
    tabs.clear()
    QTest.qWait(30)
    assert changes[-1] == -1 and all(isValid(page) and page.isHidden() for page in pages)
    checkSync(tabs)
    tabs.setTabBarAutoHide(True)
    tabs.addTab(first, 'Reuse')
    assert tabs.tabBar.isHidden() and tabs.tabBarAutoHide()
    tabs.addTab(second, 'Second')
    assert not tabs.tabBar.isHidden()
    tabs.setTabVisible(0, False)
    tabs.setTabVisible(1, False)
    tabs.setTabVisible(0, True)
    assert tabs.currentIndex() == 0
    tabs.setTabVisible(1, True)
    tabs.removeTab(0)
    assert tabs.currentWidget() is second and tabs.currentIndex() == 0 and tabs.tabBar.isHidden()
    tabs.removeTab(0)
    assert tabs.currentIndex() == -1 and changes[-1] == -1
    checkSync(tabs)
    tabs.close()

    # Conventional Qt overloads and notification timing match QTabWidget.
    for container in (QTabWidget(), RoundTabWidget()):
        seen = []
        container.currentChanged.connect(seen.append)
        one, two = QWidget(), QWidget()
        container.addTab(one, 'One')
        container.addTab(two, QIcon(), 'Two')
        container.setCurrentWidget(two)
        container.insertTab(0, QWidget(), 'Zero')
        container.removeTab(0)
        container.clear()
        assert seen == [0, 1, 1, 0, -1], seen

    demo = RoundTabWidgetDemo()
    demo.resize(760, 520)
    demo.show()
    QTest.qWait(100)
    example = demo.tabWidget
    assert example.count() == 2 and example.currentIndex() == 0
    QTest.mouseClick(example.tabBar.addButton, Qt.LeftButton)
    assert example.count() == 3 and example.currentIndex() == 2
    QTest.mouseClick(example.tabBar.currentTab().closeButton, Qt.LeftButton)
    QTest.qWait(50)
    assert example.count() == 2
    example.setCurrentIndex(0)
    # Render the unified outline alone at fractional scaling. There must be no
    # horizontal stroke under the active tab, or doubled alpha at the two joins.
    for index in (0, 1):
        example.setCurrentIndex(index)
        selected = example.tabBar.currentTab()
        selectedX = selected.mapTo(example, QPoint()).x()
        baseline = example.stackedWidget.y()
        for scale in (1, 1.25, 1.5, 1.75, 2, 3.5):
            outline = QImage(ceil(example.width() * scale), ceil(example.height() * scale),
                             QImage.Format_ARGB32_Premultiplied)
            outline.setDevicePixelRatio(scale)
            outline.fill(Qt.transparent)
            painter = QPainter(outline)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(QColor(255, 255, 255, 18), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(example._framePath(outline=True))
            painter.end()
            for x in range(ceil((selectedX + 12) * scale), int((selectedX + selected.width() - 12) * scale)):
                for y in range(int((baseline - 1) * scale), ceil((baseline + 2) * scale)):
                    assert outline.pixelColor(x, y).alpha() == 0, (index, scale, x, y)
            for join in (selectedX, selectedX + selected.width()):
                for x in range(max(0, int((join - 6) * scale)), min(outline.width(), ceil((join + 6) * scale))):
                    for y in range(int((baseline - 6) * scale), ceil((baseline + 2) * scale)):
                        assert outline.pixelColor(x, y).alpha() <= 18, (index, scale, x, y)
    example.setCurrentIndex(0)
    previews = Path(tempfile.gettempdir()) / 'fluent-round-tab-widget-previews'
    previews.mkdir(exist_ok=True)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        QTest.qWait(100)
        for dpr in (1, 2):
            image = QImage(demo.width() * dpr, demo.height() * dpr, QImage.Format_ARGB32_Premultiplied)
            image.setDevicePixelRatio(dpr)
            image.fill(Qt.transparent)
            demo.render(image)
            selected = example.tabBar.currentTab()
            point = selected.mapTo(demo, QPoint(selected.width() // 2, selected.height() - 1))
            color = '#f9f9f9' if theme == Theme.LIGHT else '#282828'
            assert image.pixelColor(point * dpr).name() == color
            content = example.stackedWidget.mapTo(demo, QPoint(40, 40))
            assert image.pixelColor(content * dpr).name() == color
            seam = example.stackedWidget.mapTo(demo, QPoint(selected.geometry().center().x(), 0))
            assert image.pixelColor(seam * dpr).name() == color, (theme, dpr, seam, image.pixelColor(seam * dpr).name())
            assert image.save(str(previews / f'{theme.value.lower()}-{dpr}x.png'))
    example.setTabSelectedBackgroundColor(QColor('#e5efff'), QColor('#324055'))
    assert example.tabBar.darkSelectedBackgroundColor.name() == '#324055'
    QTest.qWait(20)
    custom = QImage(example.size(), QImage.Format_ARGB32_Premultiplied)
    custom.fill(Qt.transparent)
    example.render(custom)
    point = example.stackedWidget.mapTo(example, QPoint(40, 40))
    assert custom.pixelColor(point).name() == '#324055'
    demo.close()
    if app.platformName() == 'windows':
        import main
        gallery = main.MainWindow()
        gallery.show()
        gallery.switchTo(gallery.buttonsInterface)
        gallery.buttonsInterface.ensureWidgetVisible(gallery.roundTabWidgetDemo.tabWidget.tabBar)
        QTest.qWait(300)
        sample = gallery.roundTabWidgetDemo.tabWidget
        setTheme(Theme.LIGHT)
        QTest.qWait(100)
        host = gallery.roundTabWidgetDemo
        preview = QImage(host.size(), QImage.Format_ARGB32_Premultiplied)
        preview.fill(Qt.transparent)
        host.render(preview)
        point = sample.mapTo(host, QPoint(1, 1))
        assert preview.pixelColor(point).name() == '#f3f4f6', preview.pixelColor(point).name()
        item = sample.tabBar.tabItem(1)
        QTest.mouseClick(gallery.windowHandle(), Qt.LeftButton, pos=item.mapTo(gallery, QPoint(45, 16)))
        assert sample.currentIndex() == 1
        QTest.mouseClick(sample.tabBar.addButton, Qt.LeftButton)
        assert sample.count() == 3
        gallery.close()
    print('PASS: RoundTabWidget Qt overloads, page ownership, signals, drag, visibility and seamless theme rendering')
    print('Previews:', previews)


if __name__ == '__main__':
    run()
