"""RoundTabBar reuses TabBar, with owned-widget interaction/rendering checks."""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QMouseEvent, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from qfluentwidgets_pro import FluentIcon, RoundTabBar, TabBar, TabCloseButtonDisplayMode, Theme, setTheme
from qfluentwidgets_pro.components.widgets.round_tab_bar import RoundTabItem
from qfluentwidgets_pro.components.widgets.tab_view import TabItem
from gallery_fixtures.round_tab_bar_demo import RoundTabBarDemo


def run():
    app = QApplication([])
    window = QWidget()
    window.resize(660, 270)
    layout = QVBoxLayout(window)
    ordinary = TabBar(window)
    layout.addWidget(ordinary)
    baseline = ordinary.addTab('baseline', 'Ordinary tab', FluentIcon.HOME)
    bar = RoundTabBar(window)
    layout.addWidget(bar)
    layout.addStretch()
    assert isinstance(bar, TabBar) and type(baseline) is TabItem
    assert ordinary.height() == 46 and baseline.height() == 36
    assert ordinary.tabMaximumWidth() == 240 and ordinary.isTabShadowEnabled()
    assert bar.height() == 38 and bar.tabMaximumWidth() == 200 and not bar.isTabShadowEnabled()
    clicked, changed, closed, added, moved, doubled = [], [], [], [], [], []
    bar.tabBarClicked.connect(clicked.append)
    bar.currentChanged.connect(changed.append)
    bar.tabCloseRequested.connect(closed.append)
    bar.tabAddRequested.connect(lambda: added.append(True))
    bar.tabMoved.connect(lambda old, new: moved.append((old, new)))
    bar.tabBarDoubleClicked.connect(doubled.append)
    callbacks = []
    first = bar.addTab('songs', 'Songs', FluentIcon.MUSIC, lambda: callbacks.append(True))
    album = bar.addTab('albums', 'Album', FluentIcon.FOLDER)
    artist = bar.addTab('artists', 'Artist')
    assert all(isinstance(item, RoundTabItem) for item in bar.items)
    assert bar.currentTab() is first and bar.count() == 3
    try:
        bar.addTab('songs', 'Duplicate')
    except ValueError:
        pass
    else:
        raise AssertionError('Duplicate route key accepted')
    window.show()
    window.activateWindow()
    QTest.qWait(100)
    setTheme(Theme.LIGHT)
    window.setObjectName('roundTabHost')
    window.setStyleSheet('QWidget#roundTabHost { background-color: #ccddee; }')
    inherited = QImage(window.size(), QImage.Format_ARGB32_Premultiplied)
    inherited.fill(Qt.transparent)
    window.render(inherited)
    assert inherited.pixelColor(bar.mapTo(window, QPoint(1, 1))).name() == '#ccddee'
    assert all(item.height() == 32 and item.y() == 6 for item in bar.items)
    assert bar.itemLayout.spacing() == 0
    assert album.x() == first.geometry().right() + 1 - 5
    assert artist.x() == album.geometry().right() + 1 - 5
    assert bar.tabRect(1).x() == album.x()
    positions = [item.pos() for item in bar.items]
    for _ in range(3):
        bar.itemLayout.setGeometry(bar.itemLayout.geometry())
        assert [item.pos() for item in bar.items] == positions
    assert album.geometry().bottom() == bar.height() - 1
    assert album.closeButton.geometry().center().y() in (15, 16)
    QTest.mouseClick(window.windowHandle(), Qt.LeftButton,
                     pos=album.mapTo(window, QPoint(60, 16)))
    assert bar.currentTab() is album and changed == [1] and clicked == [1]
    QTest.mouseClick(first, Qt.LeftButton, pos=QPoint(55, 16))
    assert bar.currentTab() is first and callbacks == [True]
    QTest.mouseDClick(artist, Qt.LeftButton, pos=QPoint(50, 16))
    assert doubled == [2]
    bar.setCurrentTab('albums')
    bar.setTabData(1, {'data': 42})
    bar.setTabText(1, 'A long album title that should fade before the close button')
    bar.setTabToolTip(1, 'Full title')
    bar.setTabTextColor(1, QColor('#ffeedd'))
    assert bar.tabData(1) == {'data': 42} and bar.tabToolTip(1) == 'Full title'
    assert bar.tabIcon(0) and bar.tab('albums') is album
    bar.setTabEnabled(0, False)
    QTest.mouseClick(first, Qt.LeftButton, pos=QPoint(50, 16))
    assert bar.currentTab() is album and len(callbacks) == 1
    bar.setTabEnabled(0, True)
    QTest.mouseClick(album.closeButton, Qt.LeftButton)
    assert closed == [1] and bar.count() == 3  # request only, no automatic deletion
    QTest.mouseClick(bar.addButton, Qt.LeftButton)
    assert added == [True] and bar.count() == 3
    for mode in TabCloseButtonDisplayMode:
        bar.setCloseButtonDisplayMode(mode)
        QTest.qWait(10)
        if mode == TabCloseButtonDisplayMode.NEVER:
            assert all(not item.closeButton.isVisible() for item in bar.items)
        elif mode == TabCloseButtonDisplayMode.ALWAYS:
            assert all(item.closeButton.isVisible() for item in bar.items)
        else:
            assert album.closeButton.isVisible()
    bar.setTabsClosable(False)
    assert not bar.tabsClosable()
    bar.setTabsClosable(True)
    inserted = bar.insertTab(0, 'inserted', 'Inserted')
    assert bar.currentTab() is album and bar.currentIndex() == 2
    bar.removeTabByKey('inserted')
    QTest.qWait(20)
    assert bar.currentTab() is album and bar.currentIndex() == 1
    bar.setTabVisible(2, False)
    assert artist.isHidden() and not bar.isTabVisible(2)
    bar.setTabVisible(2, True)
    assert artist.isVisible() and bar.isTabVisible(2)
    bar.setCurrentTab('albums')

    # Reorder using real widget event forwarding, with button state specified.
    bar.setMovable(True)
    QTest.mouseMove(window.windowHandle(), album.mapTo(window, QPoint(80, 16)))
    assert not moved and not bar.isDraging
    bar.setCurrentTab('songs')
    start = QPoint(60, 16)
    QTest.mousePress(first, Qt.LeftButton, pos=start)
    destination = QPoint(first.width() + 70, 16)
    event = QMouseEvent(QEvent.MouseMove, QPointF(destination),
                        QPointF(first.mapToGlobal(destination)), Qt.NoButton, Qt.LeftButton, Qt.NoModifier)
    app.sendEvent(first, event)
    QTest.mouseRelease(first, Qt.LeftButton, pos=QPoint(60, 16))
    QTest.qWait(300)
    assert moved == [(0, 1)], moved
    assert bar.currentTab() is first and bar.currentIndex() == 1 and not bar.isDraging
    assert [bar.itemLayout.itemAt(i).widget() for i in range(bar.count())] == bar.items
    bar.setMovable(False)

    # Scroll mode keeps fixed widths when max width is edited live.
    for index in range(8):
        bar.addTab(f'many-{index}', f'Tab {index}')
    bar.setScrollable(True)
    bar.setTabMaximumWidth(150)
    QTest.qWait(100)
    assert all(item.minimumWidth() == item.maximumWidth() == 150 for item in bar.items)
    assert bar.horizontalScrollBar().maximum() > 0, (window.size(), bar.size(), bar.view.size(),
                                                     bar.itemLayout.minimumSize(), bar.itemLayout.sizeHint())
    bar.horizontalScrollBar().setValue(180)
    assert bar.view.x() < 0
    bar.setTabMaximumWidth(190)
    assert all(item.minimumWidth() == item.maximumWidth() == 190 for item in bar.items)
    bar.setScrollable(False)
    assert all(item.minimumWidth() == bar.tabMinimumWidth() for item in bar.items)
    wheel = QWheelEvent(QPointF(20, 20), QPointF(bar.mapToGlobal(QPoint(20, 20))), QPoint(),
                        QPoint(0, -120), Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
    bar.wheelEvent(wheel)
    assert not wheel.isAccepted()

    # Shape geometry: upper corners inset, bottom flares fill out to both edges.
    bar.clear()
    QTest.qWait(30)
    assert bar.count() == 0 and bar.currentIndex() == -1
    shaped = bar.addTab('shape', 'Shape')
    bar.setTabMaximumWidth(200)
    bar.setTabSelectedBackgroundColor(QColor('#e5efff'), QColor('#324055'))
    QTest.qWait(30)
    path = shaped._selectedPath()
    assert not path.contains(QPointF(1, 1))
    assert not path.contains(QPointF(1, shaped.height() / 2))
    assert path.contains(QPointF(5.25, shaped.height() / 2))
    assert path.contains(QPointF(shaped.width() - 5.25, shaped.height() / 2))
    # Lower wings must remain visibly curved, not collapse into square corners.
    assert not path.contains(QPointF(1, shaped.height() - 3))
    assert path.contains(QPointF(4.75, shaped.height() - 1))
    # True quarter-circle wings, rather than flattened quadratic end points.
    assert not path.contains(QPointF(3.4, shaped.height() - 1.5))
    assert path.contains(QPointF(3.8, shaped.height() - 1.5))
    assert shaped._selectedPath(outline=True).elementCount() < path.elementCount()
    assert path.contains(QPointF(3, shaped.height() - .2))
    assert path.contains(QPointF(shaped.width() - 3, shaped.height() - .2))
    assert path.contains(QPointF(shaped.width() / 2, shaped.height() - .2))
    for theme, color in ((Theme.LIGHT, '#e5efff'), (Theme.DARK, '#324055')):
        setTheme(theme)
        QTest.qWait(30)
        image = QImage(shaped.width() * 2, shaped.height() * 2, QImage.Format_ARGB32_Premultiplied)
        image.setDevicePixelRatio(2)
        image.fill(Qt.transparent)
        shaped.render(image, renderFlags=QWidget.DrawChildren)
        assert image.pixelColor(shaped.width(), shaped.height() * 2 - 1).name() == color
        # The 1px top outline is visible; the middle of the bottom is still open.
        assert image.pixelColor(shaped.width(), 0).name() != color

    # The actual demo owns pages and handles the add/close requests.
    demo = RoundTabBarDemo()
    demo.resize(900, 310)
    demo.show()
    QTest.qWait(100)
    assert demo.stack.currentWidget() is demo.pages['albums']
    QTest.mouseClick(demo.tabBar.addButton, Qt.LeftButton)
    assert demo.tabBar.count() == 4 and demo.stack.currentWidget() is demo.pages['new-1']
    QTest.mouseClick(demo.tabBar.currentTab().closeButton, Qt.LeftButton)
    QTest.qWait(30)
    assert demo.tabBar.count() == 3 and 'new-1' not in demo.pages
    demo.movableCheckBox.setChecked(True)
    demo.scrollableCheckBox.setChecked(True)
    demo.maximumWidthBox.setValue(180)
    assert demo.tabBar.isMovable() and demo.tabBar.isScrollable()
    assert demo.tabBar.tabMaximumWidth() == 180
    demo.closeModeBox.setCurrentIndex(2)
    assert not demo.tabBar.tabsClosable()
    demo.scrollableCheckBox.setChecked(False)
    demo.maximumWidthBox.setValue(200)
    demo.closeModeBox.setCurrentIndex(0)
    demo.tabBar.setCurrentTab('albums')
    demo._syncPage()
    previews = Path(tempfile.gettempdir()) / 'fluent-round-tab-previews'
    previews.mkdir(exist_ok=True)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        QTest.qWait(150)
        for dpr in (1, 2):
            image = QImage(demo.width() * dpr, demo.height() * dpr, QImage.Format_ARGB32_Premultiplied)
            image.setDevicePixelRatio(dpr)
            image.fill(Qt.transparent)
            demo.render(image)
            if theme == Theme.LIGHT:
                # The standalone bar inherits its host background, without
                # baking the main.py demonstration background into the widget.
                for key in ('albums', 'songs', 'artists'):
                    demo.tabBar.setCurrentTab(key)
                    demo._syncPage()
                    image.fill(Qt.transparent)
                    demo.render(image)
                    selected = demo.tabBar.currentTab()
                    tabPoint = selected.mapTo(demo, QPoint(selected.width() // 2, 2))
                    stripPoint = demo.tabBar.mapTo(demo, QPoint(10, 1))
                    selectedColor = image.pixelColor(tabPoint * dpr)
                    stripColor = image.pixelColor(stripPoint * dpr)
                    assert selectedColor.name() == '#f9f9f9', selectedColor.name()
                    assert stripColor.name() == '#f9f9f9', stripColor.name()
                demo.tabBar.setCurrentTab('albums')
                demo._syncPage()
                image.fill(Qt.transparent)
                demo.render(image)
            assert image.save(str(previews / f'{theme.value.lower()}-{dpr}x.png'))
    demo.close()
    window.close()
    if app.platformName() == 'windows':
        example = RoundTabBarDemo()
        example.show()
        QTest.qWait(350)
        setTheme(Theme.LIGHT)
        QTest.qWait(100)
        item = example.tabBar.tab('songs')
        QTest.mouseClick(item, Qt.LeftButton, pos=QPoint(50, 16))
        assert example.stack.currentWidget() is example.pages['songs']
        QTest.mouseClick(example.tabBar.addButton, Qt.LeftButton)
        assert example.tabBar.count() == 4 and example.tabBar.currentTab().routeKey() == 'new-1'
        QTest.mouseClick(example.tabBar.currentTab().closeButton, Qt.LeftButton)
        QTest.qWait(30)
        assert example.tabBar.count() == 3 and example.stack.count() == 3
        example.close()
    print('PASS: RoundTabBar reuse, add/close, routes, callbacks, drag, scroll, modes and seam/DPI rendering')
    print('Previews:', previews)


if __name__ == '__main__':
    run()
