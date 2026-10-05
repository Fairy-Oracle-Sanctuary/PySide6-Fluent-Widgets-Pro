"""Run with py -3.9 tests/check_flyout_dialog.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QWidget, QLineEdit
from PySide6.QtTest import QTest
from qfluentwidgets_pro import FlyoutDialog, FlyoutAnimationType, Theme, setTheme


def run():
    app = QApplication([])
    owner = QWidget()
    owner.resize(600, 500)
    target = QPushButton('Show dialog', owner)
    target.move(250, 300)
    owner.show()
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        for action in ('accept', 'cancel', 'outside', 'close'):
            dialog = FlyoutDialog('Title', 'This is a custom flyout dialog.')
            editor = QLineEdit()
            dialog.addWidget(editor)
            results = []
            dialog.accepted.connect(lambda: results.append('accepted'))
            dialog.rejected.connect(lambda: results.append('rejected'))
            popup = dialog.showAt(target, owner, FlyoutAnimationType.NONE)
            QTest.qWait(30)
            assert popup.isVisible() and editor.isVisible()
            QTest.mouseClick(editor, Qt.LeftButton)
            assert popup.isVisible() and results == []
            assert dialog.buttonBar.height() == 40
            assert dialog.minimumWidth() == 256
            assert dialog.viewLayout.contentsMargins().left() + dialog.vBoxLayout.contentsMargins().left() == 16
            assert dialog.viewLayout.spacing() == 8
            for button in (dialog.yesButton, dialog.cancelButton):
                assert button.toolTip() == ''
                assert button.accessibleName()
                assert button.height() == 32
                assert button.width() >= (dialog.buttonBar.width() - 8) // 2
            # Hover fill extends across the half-width action, not a small icon box.
            dialog.yesButton.setAttribute(Qt.WA_UnderMouse, True)
            QApplication.sendEvent(dialog.yesButton, QEvent(QEvent.Enter))
            QTest.qWait(30)
            hover = dialog.yesButton.grab().toImage()
            dialog.yesButton.setAttribute(Qt.WA_UnderMouse, False)
            QApplication.sendEvent(dialog.yesButton, QEvent(QEvent.Leave))
            QTest.qWait(30)
            normal = dialog.yesButton.grab().toImage()
            dpr = hover.devicePixelRatio()
            sample = QPoint(round(8 * dpr), round(16 * dpr))
            assert hover.pixelColor(sample) != normal.pixelColor(sample)
            dialog.grab()
            if action == 'accept':
                dialog.yesButton.click()
            elif action == 'cancel':
                dialog.cancelButton.click()
            elif action == 'outside':
                QTest.mouseClick(owner, Qt.LeftButton, pos=QPoint(10, 450))
            else:
                popup.close()
            assert results == ['accepted' if action == 'accept' else 'rejected']
            assert not popup.isVisible()
            QTest.qWait(30)
    owner.close()
    print('PASS: custom content, themes, confirm, cancel and dismissal')


if __name__ == '__main__':
    run()
