"""Native window regression: py -3.9 tests/check_filled_window.py [--preview]."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem, QWidget

from gallery_fixtures.filled_window_demo import FilledWindowDemo
from qfluentwidgets_pro import FluentIcon, FluentWindow, Theme, setTheme, setThemeColor, themeColor
from qfluentwidgets_pro.components.navigation.navigation_widget import NavigationWidget


def run():
    app = QApplication([])
    ordinary = FluentWindow()
    normal_page = QWidget(ordinary)
    normal_page.setObjectName('ordinaryPage')
    normal_item = ordinary.addSubInterface(normal_page, FluentIcon.HOME, 'Normal')
    shared_width = NavigationWidget.EXPAND_WIDTH
    window = FilledWindowDemo()
    assert NavigationWidget.EXPAND_WIDTH == shared_width
    assert normal_item.EXPAND_WIDTH == shared_width
    window.show()
    window.setMicaEffectEnabled(True)
    panel = window.navigationInterface.panel
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        for color in ('#009faa', '#8764b8'):
            setThemeColor(color)
            window.switchTo(window.homeInterface)
            QTest.qWait(350)
            item = panel.widget('filledHome').itemWidget
            assert item.isSelected
            actual = item.grab().toImage().pixelColor(5, 5)
            expected = themeColor()
            assert actual.rgb() == expected.rgb(), (theme, color, actual.name(), expected.name())
            assert not panel.indicator.isVisible()
            panel.widget('filledMusic').click()
            QTest.qWait(350)
            assert window.stackedWidget.currentWidget().objectName() == 'filledMusic'
            assert panel.widget('filledMusic').isSelected
            assert not panel.widget('filledHome').isSelected

    for width, height in ((600, 400), (1200, 800), (920, 700)):
        window.resize(width, height)
        QTest.qWait(30)
        assert window.navigationInterface.width() == 216
        assert window.titleBar.x() == 0 and window.titleBar.width() == window.width()
        assert window.stackedWidget.x() == 216
        assert window.stackedWidget.y() == window.titleBar.height()
        assert panel.widget('filledSettings').geometry().bottom() < panel.height()
    window.navigationInterface.setExpandWidth(260)
    QTest.qWait(30)
    assert window.navigationInterface.width() == 260
    assert panel.widget('filledHome').width() == 236
    assert panel.widget('filledHome').itemWidget.width() == 236
    assert NavigationWidget.EXPAND_WIDTH == shared_width
    window.navigationInterface.setExpandWidth(216)
    window.searchLineEdit.setText('视频')
    window.searchLineEdit.search()
    QTest.qWait(30)
    popup = window._searchPopup
    assert popup.isVisible() and popup.view.count() == 1
    assert popup.width() == window.searchLineEdit.width() + 20
    assert popup.view.verticalScrollBar().maximum() == 0
    assert popup.view.currentItem().data(Qt.UserRole) == 'filledVideo'
    option = QStyleOptionViewItem()
    popup.view.delegate.initStyleOption(option, popup.view.currentIndex())
    assert option.icon.pixmap(option.decorationSize, QIcon.Normal).toImage() == \
        option.icon.pixmap(option.decorationSize, QIcon.Selected).toImage()
    QTest.keyClick(window.searchLineEdit, Qt.Key_Return)
    QTest.qWait(350)
    assert window.stackedWidget.currentWidget().objectName() == 'filledVideo'
    assert not popup.isVisible()
    window.searchLineEdit.clear()
    assert window.stackedWidget.currentWidget().objectName() == 'filledVideo'
    window.searchLineEdit.setText('不存在')
    window.searchLineEdit.search()
    assert popup.view.count() == 0 and popup.emptyLabel.isVisible()
    QTest.keyClick(window.searchLineEdit, Qt.Key_Return)
    assert window.stackedWidget.currentWidget().objectName() == 'filledVideo'
    QTest.keyClick(window.searchLineEdit, Qt.Key_Escape)
    assert not popup.isVisible()
    extras = []
    for index in range(24):
        page = QWidget(window)
        page.setObjectName('searchPage' + str(index))
        window.addSubInterface(page, FluentIcon.FOLDER, 'Video page ' + str(index))
        extras.append(page)
    window.searchLineEdit.setText('VIDEO page')
    window.searchLineEdit.search()
    QTest.qWait(30)
    assert popup.view.count() == 24
    assert popup.view.verticalScrollBar().maximum() > 0
    QTest.keyClick(window.searchLineEdit, Qt.Key_Down)
    assert popup.view.currentRow() == 1
    window.removeInterface(extras.pop(0), isDelete=True)
    assert popup.view.count() == 23
    assert popup.view.currentItem().data(Qt.UserRole) == 'searchPage1'
    QTest.keyClick(window.searchLineEdit, Qt.Key_Return)
    QTest.qWait(350)
    assert window.stackedWidget.currentWidget().objectName() == 'searchPage1'
    window.searchLineEdit.clear()
    window.switchTo(window.homeInterface)
    QTest.qWait(350)
    for page in extras:
        window.removeInterface(page, isDelete=True)
    assert window._pageSearchResults('设置')[0][0] == 'filledSettings'
    extra = QWidget(window)
    extra.setObjectName('filledExtra')
    window.addSubInterface(extra, FluentIcon.FOLDER, 'Extra')
    window.removeInterface(extra, isDelete=True)
    QTest.qWait(30)
    assert 'filledExtra' not in panel.items
    assert window.stackedWidget.count() == 5
    ordinary.close()
    print('PASS: light/dark, custom accent, navigation, search, resize, width isolation, removal', flush=True)
    if '--preview' in sys.argv:
        setTheme(Theme.LIGHT)
        setThemeColor('#009faa')
        window.switchTo(window.homeInterface)
        window.setWindowTitle('FilledFluentWindow visual check')
        QTimer.singleShot(60000, app.quit)
        app.exec()
    window.close()


if __name__ == '__main__':
    run()
