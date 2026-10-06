"""GuideWindow's native shell, custom pages, existing pips and lifecycle."""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QLocale, QPoint, QSize, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget
from shiboken6 import isValid

from qfluentwidgets_pro import FluentTranslator, GuideWindow, PipsPager, Theme, setTheme
from qfluentwidgets_pro.qframelesswindow import FramelessWindow
from gallery.view.guide_window_demo import GuideWindowDemo


class ValidatedGuide(GuideWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.allowForward = True
        self.validations = []

    def validatePage(self, page):
        self.validations.append(page)
        return self.allowForward


def run():
    app = QApplication([])
    owner = QWidget()
    owner.resize(950, 650)
    owner.move(20, 20)
    owner.show()
    guide = ValidatedGuide(owner)
    assert guide.isWindow() and not guide.isModal()
    micaSupported = sys.platform == 'win32' and sys.getwindowsversion().build >= 22000
    assert not guide.isVisible() and guide.isMicaEffectEnabled() == micaSupported
    assert GuideWindow.__bases__ == (FramelessWindow,)
    assert guide.parentWidget() is None
    assert isinstance(guide.pipsPager, PipsPager)
    assert guide.size() == QSize(670, 460)
    assert guide.currentIndex() == -1 and guide.count() == 0
    assert not guide.nextButton.isEnabled() and not guide.next()
    assert not guide.finish()
    pages = [QWidget() for _ in range(3)]
    form = QVBoxLayout(pages[1])
    field = QLineEdit(pages[1])
    form.addWidget(field)
    for index, page in enumerate(pages):
        assert guide.addPage(page) == index
    assert guide.count() == 3 and guide.page(1) is pages[1]
    assert guide.pipsPager.getPageNumber() == 3
    assert guide.currentIndex() == 0 and guide.pipsPager.currentIndex() == 0
    try:
        guide.addPage(pages[0])
    except ValueError:
        pass
    else:
        raise AssertionError('Duplicate page accepted')
    for operation in (lambda: guide.setCurrentIndex(3), lambda: guide.insertPage(-1, QWidget())):
        try:
            operation()
        except IndexError:
            pass
        else:
            raise AssertionError('Invalid index accepted')
    changes, finished, cancelled = [], [], []
    guide.currentIndexChanged.connect(changes.append)
    guide.finished.connect(lambda: finished.append(True))
    guide.cancelled.connect(lambda: cancelled.append(True))
    guide.show()
    guide.activateWindow()
    QTest.qWait(150)
    assert not guide.titleBar.minBtn.isVisible() and not guide.titleBar.maxBtn.isVisible()
    assert not hasattr(guide.titleBar, 'iconLabel') and not hasattr(guide.titleBar, 'titleLabel')
    if app.platformName() == 'windows':
        import ctypes
        import win32con
        import win32gui
        hwnd = int(guide.winId())
        assert win32gui.IsWindowVisible(hwnd)
        assert win32gui.GetWindow(hwnd, win32con.GW_OWNER) == 0
        exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        assert not exstyle & (win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_LAYERED)
        assert exstyle & win32con.WS_EX_APPWINDOW
        if micaSupported and sys.getwindowsversion().build >= 22523:
            backdrop = ctypes.c_int()
            result = guide.windowEffect.dwmapi.DwmGetWindowAttribute(
                ctypes.c_void_p(hwnd), 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
            assert result == 0 and backdrop.value == 2  # DWMSBT_MAINWINDOW / Mica.
            guide.setMicaEffectEnabled(False)
            guide.windowEffect.dwmapi.DwmGetWindowAttribute(
                ctypes.c_void_p(hwnd), 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
            assert backdrop.value == 1  # DWMSBT_NONE, not just covered by solid paint.
            guide.setMicaEffectEnabled(True)
            guide.windowEffect.dwmapi.DwmGetWindowAttribute(
                ctypes.c_void_p(hwnd), 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
            assert backdrop.value == 2
    assert not guide.previousButton.isVisible()
    assert guide.footer.height() == 80
    assert guide.footer.geometry().bottom() == guide.rect().bottom()
    assert guide.stackedWidget.y() == guide.titleBar.height()
    assert guide.titleBar.width() == guide.width()

    guide.allowForward = False
    assert not guide.next() and guide.currentIndex() == 0
    assert guide.validations[-1] is pages[0]
    guide.pipsPager.setCurrentIndex(2)
    QTest.qWait(30)
    assert guide.currentIndex() == 0 and guide.pipsPager.currentIndex() == 0
    assert not changes
    guide.allowForward = True
    guide.setNextEnabled(False)
    assert not guide.nextButton.isEnabled() and not guide.next()
    guide.pipsPager.setCurrentIndex(1)
    QTest.qWait(30)
    assert guide.currentIndex() == 0 and guide.pipsPager.currentIndex() == 0
    guide.setNextEnabled(True)
    QTest.mouseClick(guide.nextButton, Qt.LeftButton)
    assert guide.currentIndex() == 1 and guide.currentPage() is pages[1]
    assert guide.pipsPager.currentIndex() == 1 and guide.previousButton.isVisible()
    field.setText('custom page value')
    QTest.mouseClick(guide.previousButton, Qt.LeftButton)
    assert guide.currentIndex() == 0 and guide.pipsPager.currentIndex() == 0
    guide.pipsPager.setCurrentIndex(1)
    QTest.qWait(30)
    assert guide.currentIndex() == 1 and field.text() == 'custom page value'

    # Actual click on the third pip and keyboard selection both drive the stack.
    rect = guide.pipsPager.visualItemRect(guide.pipsPager.item(2))
    QTest.mouseClick(guide.pipsPager.viewport(), Qt.LeftButton, pos=rect.center())
    QTest.qWait(40)
    assert guide.currentIndex() == 2 and guide.nextButton.text() == 'Finish'
    QTest.keyClick(guide.pipsPager, Qt.Key_Left)
    QTest.qWait(40)
    assert guide.currentIndex() == 1 and guide.pipsPager.currentIndex() == 1
    guide.setStepNavigationEnabled(False)
    assert not guide.pipsPager.isEnabled()
    assert guide.next() and guide.currentIndex() == 2
    guide.allowForward = False
    assert not guide.finish() and not finished
    guide.allowForward = True
    QTest.mouseClick(guide.nextButton, Qt.LeftButton)
    assert finished == [True] and not cancelled and not guide.isVisible()
    assert not guide.finish() and finished == [True]
    guide.show()
    guide.activateWindow()
    guide.setCurrentIndex(1)
    # Native foreground activation can be denied by Windows in an automated run.
    # Scope the synthetic shortcut test to this application's own active window.
    app.setActiveWindow(guide)
    field.setFocus()
    QTest.qWait(100)
    QTest.keyClick(field, Qt.Key_Escape)
    QTest.qWait(30)
    assert cancelled == [True] and finished == [True] and not guide.isVisible()
    assert field.text() == 'custom page value'
    guide.show()
    guide.activateWindow()
    QTest.qWait(80)
    QTest.mouseClick(guide.titleBar.closeBtn, Qt.LeftButton)
    assert cancelled == [True, True] and not guide.isVisible(), (cancelled, guide.isVisible(), guide.titleBar.closeBtn.isVisible(), guide.titleBar.closeBtn.geometry())
    assert owner.isVisible()  # Close must never target the window that owns the guide.

    # Insert/remove before the current page preserves page identity and pips.
    guide.setCurrentIndex(1)
    extra = QWidget()
    guide.insertPage(0, extra)
    assert guide.currentPage() is pages[1] and guide.currentIndex() == 2
    assert guide.pipsPager.currentIndex() == 2 and guide.pipsPager.getPageNumber() == 4
    guide.removePage(extra)
    assert guide.currentIndex() == 1 and isValid(extra)
    assert extra.parentWidget() is None and not extra.isVisible()
    guide.removePage(pages[1])
    assert guide.count() == 2 and guide.currentPage() is not pages[1]
    assert isValid(pages[1]) and field.text() == 'custom page value'
    for page in (pages[0], pages[2]):
        guide.removePage(page)
    assert guide.count() == 0 and guide.pipsPager.currentIndex() == -1
    assert not guide.nextButton.isEnabled() and guide.currentIndex() == -1
    guide.addPage(pages[0])
    assert guide.currentIndex() == 0 and guide.nextButton.text() == 'Finish'
    guide.addPage(pages[1])
    guide.addPage(pages[2])
    pages[2].deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    assert guide.count() == 2 and guide.pipsPager.getPageNumber() == 2

    # A real reference-like form supplied by the demo, light/dark and 1x/2x.
    demo = GuideWindowDemo(owner)
    demo.show()
    QTest.qWait(150)
    previews = Path(tempfile.gettempdir()) / 'fluent-guide-window-previews'
    previews.mkdir(exist_ok=True)
    # Native Mica is composited by DWM, not included in QWidget.render(). Render
    # solid fallback previews while checking the actual native backdrop above.
    demo.setMicaEffectEnabled(False)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        QTest.qWait(160)
        for width, height in ((670, 460), (960, 660)):
            demo.resize(width, height)
            QTest.qWait(40)
            assert demo.footer.geometry().bottom() == demo.rect().bottom()
            assert demo.stackedWidget.geometry().bottom() + 1 == demo.footer.y()
            assert demo.titleBar.width() == demo.width(), (width, demo.size(), demo.titleBar.size())
            assert demo.previousButton.geometry().right() < demo.nextButton.x()
        demo.resize(670, 460)
        QTest.qWait(40)
        for dpr in (1, 2):
            image = QImage(demo.width() * dpr, demo.height() * dpr, QImage.Format_ARGB32_Premultiplied)
            image.setDevicePixelRatio(dpr)
            image.fill(Qt.transparent)
            demo.render(image)
            assert image.save(str(previews / f'{theme.value.lower()}-{dpr}x.png'))
    assert demo.tokenEdit.echoMode() == QLineEdit.EchoMode.Password
    demo.setMicaEffectEnabled(True)
    assert demo.isMicaEffectEnabled() == micaSupported
    demo.close()
    guide.close()
    translator = FluentTranslator(QLocale(QLocale.Chinese, QLocale.China))
    app.installTranslator(translator)
    localized = GuideWindow()
    localized.addPage(QWidget())
    localized.addPage(QWidget())
    assert localized.previousButton.text() == '上一步' and localized.nextButton.text() == '下一步'
    localized.setCurrentIndex(1)
    assert localized.nextButton.text() == '完成'
    app.removeTranslator(translator)
    localized.close()
    owner.close()
    centeringParent = QWidget()
    independent = GuideWindow(centeringParent)
    independent.addPage(QWidget())
    independent.show()
    assert independent.parentWidget() is None
    centeringParent.deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    assert not independent.isVisible()
    independent.deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    if app.platformName() == 'windows':
        import main
        gallery = main.MainWindow()
        gallery.show()
        gallery.activateWindow()
        gallery.switchTo(gallery.buttonsInterface)
        gallery.buttonsInterface.ensureWidgetVisible(gallery.guideWindowButton)
        QTest.qWait(350)
        button = gallery.guideWindowButton
        QTest.mouseClick(gallery.windowHandle(), Qt.LeftButton,
                         pos=button.mapTo(gallery, button.rect().center()))
        QTest.qWait(100)
        wizard = gallery._guideWindow
        assert wizard.isVisible() and wizard.parentWidget() is None and wizard.isWindow()
        assert wizard.isMicaEffectEnabled() == micaSupported
        wizard.setCurrentIndex(2)
        wizard.next()
        assert not wizard.isVisible() and gallery.isVisible()
        assert '已完成' in button.text()
        gallery._openGuideWindow()
        QTest.qWait(100)
        QTest.mouseClick(wizard.titleBar.closeBtn, Qt.LeftButton)
        assert not wizard.isVisible() and gallery.isVisible() and '已取消' in button.text()
        gallery.close()
    print('PASS: GuideWindow custom pages, PipsPager, navigation, validation, close/finish/reuse, theme and DPI')
    print('Previews:', previews)


if __name__ == '__main__':
    run()
