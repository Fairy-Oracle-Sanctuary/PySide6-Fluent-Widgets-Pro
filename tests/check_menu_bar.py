"""MenuBar actions, popup switching and keyboard navigation; owned UI only."""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QAction, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget

from qfluentwidgets_pro import MenuBar, RoundMenu, Theme, setTheme


def run():
    app = QApplication([])
    window = QWidget()
    window.resize(660, 410)
    layout = QVBoxLayout(window)
    bar = MenuBar(window)
    layout.addWidget(bar)
    field = QLineEdit(window)
    layout.addWidget(field)
    layout.addStretch()
    fileMenu = bar.addMenu('文件(&F)')
    opened = QAction('打开文件...', window, shortcut='Ctrl+O')
    fileMenu.addAction(opened)
    disabled = QAction('Disabled', window)
    disabled.setEnabled(False)
    fileMenu.addAction(disabled)
    fileMenu.addSeparator()
    last = QAction('新建文本文件', window)
    fileMenu.addAction(last)
    editMenu = bar.addMenu('编辑(&E)')
    toggle = QAction('Toggle', window, checkable=True)
    editMenu.addAction(toggle)
    sub = RoundMenu('Submenu', editMenu)
    nested = QAction('Nested', window, shortcut='Ctrl+J')
    sub.addAction(nested)
    editMenu.addMenu(sub)
    command = QAction('Command', window)
    bar.addAction(command)
    seen = []
    bar.triggered.connect(seen.append)
    window.show()
    window.activateWindow()
    field.setFocus()
    QTest.qWait(100)
    assert bar.height() == 32 and bar.menus() == [fileMenu, editMenu]
    assert bar._buttons[fileMenu.menuAction()].height() == 32

    def clickHeader(menu):
        button = bar._buttons[menu.menuAction()]
        QTest.mouseClick(window.windowHandle(), Qt.LeftButton,
                         pos=button.mapTo(window, button.rect().center()))
        QTest.qWait(50)

    def key(key, modifiers=Qt.NoModifier):
        if app.platformName() == 'offscreen' and bar.activeMenu() is None:
            # The headless backend can leave a hidden popup as activeWindow.
            app.setActiveWindow(window)
        target = QApplication.focusWidget() or field
        QTest.keyClick(target, key, modifiers)
        QTest.qWait(30)

    def closed():
        assert bar.activeMenu() is None and not bar._filterInstalled
        assert not fileMenu.isVisible() and not editMenu.isVisible() and not sub.isVisible()

    clickHeader(fileMenu)
    assert bar.activeMenu() is fileMenu and fileMenu.isVisible()
    margins = fileMenu.layout().contentsMargins()
    button = bar._buttons[fileMenu.menuAction()]
    assert fileMenu.pos().x() + margins.left() == button.mapToGlobal(QPoint()).x() + 12
    assert fileMenu.pos().y() + margins.top() == button.mapToGlobal(QPoint()).y() + 39
    clickHeader(fileMenu)
    closed()
    clickHeader(fileMenu)
    button = bar._buttons[editMenu.menuAction()]
    QTest.mouseMove(window.windowHandle(), button.mapTo(window, button.rect().center()))
    QTest.qWait(80)
    assert bar.activeMenu() is editMenu and not fileMenu.isVisible() and editMenu.isVisible()
    key(Qt.Key_Escape)
    closed()
    # A closed bar does not open a menu merely from hovering.
    QTest.mouseMove(window.windowHandle(), bar._buttons[fileMenu.menuAction()].mapTo(window, QPoint(10, 10)))
    QTest.qWait(30)
    closed()

    bar.setActiveMenu(fileMenu)
    assert fileMenu.view.currentRow() == 0
    key(Qt.Key_Down)
    assert fileMenu.view.currentRow() == 3  # skip disabled item and separator
    key(Qt.Key_Home)
    assert fileMenu.view.currentRow() == 0
    key(Qt.Key_End)
    assert fileMenu.view.currentRow() == 3
    key(Qt.Key_Return)
    closed()
    assert seen == [last]

    bar.setActiveMenu(fileMenu)
    key(Qt.Key_Right)
    assert bar.activeMenu() is editMenu and editMenu.view.currentRow() == 0, (bar.activeMenu(), editMenu.view.currentRow())
    key(Qt.Key_Return)
    assert toggle.isChecked() and seen[-1] is toggle
    closed()
    bar.setActiveMenu(editMenu)
    key(Qt.Key_Down)
    key(Qt.Key_Right)
    QTest.qWait(280)
    assert sub.isVisible() and bar.activeMenu() is editMenu
    key(Qt.Key_Left)
    assert not sub.isVisible() and editMenu.isVisible()
    key(Qt.Key_Right)
    QTest.qWait(280)
    key(Qt.Key_Return)
    assert seen[-1] is nested
    closed()

    field.setFocus()
    key(Qt.Key_O, Qt.ControlModifier)
    assert seen[-1] is opened
    count = len(seen)
    fileMenu.menuAction().setEnabled(False)
    key(Qt.Key_O, Qt.ControlModifier)
    assert len(seen) == count
    fileMenu.menuAction().setEnabled(True)
    fileMenu.menuAction().setVisible(False)
    key(Qt.Key_O, Qt.ControlModifier)
    assert len(seen) == count
    fileMenu.menuAction().setVisible(True)
    bar.setActiveMenu(fileMenu)
    key(Qt.Key_O, Qt.ControlModifier)
    assert len(seen) == count + 1 and seen[-1] is opened
    closed()
    bar.removeMenu(fileMenu)
    key(Qt.Key_O, Qt.ControlModifier)
    assert len(seen) == count + 1
    bar.insertMenu(editMenu, fileMenu)
    QTest.qWait(30)
    field.setFocus()
    key(Qt.Key_O, Qt.ControlModifier)
    assert len(seen) == count + 2
    extra = QAction('Extra', window, shortcut='Ctrl+K')
    fileMenu.addAction(extra)
    key(Qt.Key_K, Qt.ControlModifier)
    assert seen[-1] is extra
    fileMenu.removeAction(extra)
    count = len(seen)
    key(Qt.Key_K, Qt.ControlModifier)
    assert len(seen) == count

    # Qt mnemonic shortcut, F10 focus and direct command headers.
    field.setFocus()
    key(Qt.Key_F, Qt.AltModifier)
    QTest.qWait(180)  # QAbstractButton mnemonic uses animateClick().
    assert bar.activeMenu() is fileMenu
    assert fileMenu.view.currentRow() == 0
    key(Qt.Key_F10)
    closed()
    field.setFocus()
    key(Qt.Key_F10)
    assert bar.hasFocus()
    key(Qt.Key_Right)
    key(Qt.Key_Down)
    assert bar.activeMenu() is editMenu
    key(Qt.Key_Right)
    closed()
    assert bar._keyboardAction is command and bar.hasFocus()
    key(Qt.Key_Return)
    assert seen[-1] is command
    key(Qt.Key_Escape)
    field.setFocus()

    bar.setActiveMenu(fileMenu)
    fileMenu.menuAction().setEnabled(False)
    closed()
    fileMenu.menuAction().setEnabled(True)
    bar.setActiveMenu(fileMenu)
    bar.setEnabled(False)
    closed()
    count = len(seen)
    key(Qt.Key_O, Qt.ControlModifier)
    assert len(seen) == count
    bar.setEnabled(True)
    bar.setActiveMenu(fileMenu)
    bar.hide()
    closed()
    bar.show()
    bar.setActiveMenu(fileMenu)
    window.resize(670, 420)
    QTest.qWait(30)
    closed()
    bar.setActiveMenu(fileMenu)
    fileMenu.hide()  # native outside dismissal also produces Hide without Close
    closed()
    bar.setActiveMenu(fileMenu)
    QTest.mouseClick(window.windowHandle(), Qt.LeftButton, pos=QPoint(600, 350))
    QTest.qWait(40)
    closed()

    # Long titles/visibility update layout, and existing menus are reusable.
    action = editMenu.menuAction()
    width = bar._buttons[action].width()
    editMenu.setTitle('A much longer menu title (&E)')
    assert bar._buttons[action].width() > width
    editMenu.setTitle('编辑(&E)')
    action.setVisible(False)
    assert not bar._buttons[action].isVisible()
    action.setVisible(True)
    spare = RoundMenu('Spare', window)
    bar.insertMenu(fileMenu, spare)
    assert bar.menus()[0] is spare
    bar.removeMenu(spare)
    bar.addMenu(spare)
    bar.removeMenu(spare)
    try:
        bar.addMenu(sub)
    except TypeError:
        pass
    else:
        raise AssertionError('Submenus cannot also be top-level menus')

    # Only render this task's widgets, with light/dark and 1x/2x previews.
    previews = Path(tempfile.gettempdir()) / 'fluent-menu-bar-previews'
    previews.mkdir(exist_ok=True)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        bar.setActiveMenu(fileMenu)
        QTest.qWait(40)
        for dpr in (1, 2):
            image = QImage(400 * dpr, 220 * dpr, QImage.Format_ARGB32_Premultiplied)
            image.setDevicePixelRatio(dpr)
            image.fill('#ffffff' if theme == Theme.LIGHT else '#202020')
            painter = QPainter(image)
            bar.render(painter, QPoint(14, 10), renderFlags=QWidget.DrawChildren)
            fileMenu.render(painter, QPoint(14, 43))
            painter.end()
            assert image.save(str(previews / f'{theme.value.lower()}-{dpr}x.png'))
        bar.closeActiveMenu()
    bar.clear()
    assert not bar.actions() and not bar._leafActions and not bar._watchedMenus
    bar.addMenu(fileMenu)
    assert fileMenu.menuActions()[0] is opened
    bar.setActiveMenu(fileMenu)
    window.hide()
    closed()
    window.close()

    # Deleting a bar must also dismiss a supplied, independently-owned menu.
    owner = QWidget()
    owner.resize(600, 350)
    external = RoundMenu('External', owner)
    external.addAction(QAction('Action', owner))
    disposable = MenuBar(owner)
    disposable.resize(500, 32)
    disposable.addMenu(external)
    owner.show()
    QTest.qWait(50)
    disposable.setActiveMenu(external)
    disposable.deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    assert not external.isVisible()
    owner.close()

    # Exercise the actual gallery page, including its menu action feedback.
    if app.platformName() == 'windows':
        import main
        gallery = main.MainWindow()
        gallery.show()
        gallery.activateWindow()
        gallery.switchTo(gallery.buttonsInterface)
        gallery.buttonsInterface.ensureWidgetVisible(gallery.menuBarDemo)
        QTest.qWait(350)
        demo = gallery.menuBarDemo
        menu = demo.menuBar.menus()[0]
        button = demo.menuBar._buttons[menu.menuAction()]
        QTest.mouseClick(gallery.windowHandle(), Qt.LeftButton,
                         pos=button.mapTo(gallery, button.rect().center()))
        QTest.qWait(50)
        assert demo.menuBar.activeMenu() is menu
        QTest.keyClick(menu.view, Qt.Key_Down)
        QTest.keyClick(menu.view, Qt.Key_Return)
        assert demo.openAction.text() in demo.statusLabel.text()
        assert demo.menuBar.activeMenu() is None
        for theme in (Theme.LIGHT, Theme.DARK):
            setTheme(theme)
            demo.menuBar._activateAction(menu.menuAction())
            QTest.qWait(50)
            dpr = 1.25
            image = QImage(500, 310, QImage.Format_ARGB32_Premultiplied)
            image.setDevicePixelRatio(dpr)
            image.fill('#ffffff' if theme == Theme.LIGHT else '#202020')
            painter = QPainter(image)
            demo.menuBar.render(painter, QPoint(11, 8), renderFlags=QWidget.DrawChildren)
            menu.render(painter, QPoint(11, 39))
            painter.end()
            assert image.save(str(previews / f'gallery-{theme.value.lower()}.png'))
            demo.menuBar.closeActiveMenu()
        gallery.close()
    print('PASS: MenuBar actions, shortcuts, popup switching, keyboard, lifecycle and previews')
    print('Previews:', previews)


if __name__ == '__main__':
    run()
