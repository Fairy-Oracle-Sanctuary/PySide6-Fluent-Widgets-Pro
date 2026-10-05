"""Run with py -3.9 tests/check_flyout_dialog.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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
        for action in ('accept', 'cancel', 'outside'):
            dialog = FlyoutDialog('Title', 'This is a custom flyout dialog.')
            editor = QLineEdit()
            dialog.addWidget(editor)
            results = []
            dialog.accepted.connect(lambda: results.append('accepted'))
            dialog.rejected.connect(lambda: results.append('rejected'))
            popup = dialog.showAt(target, owner, FlyoutAnimationType.NONE)
            QTest.qWait(30)
            assert popup.isVisible() and editor.isVisible()
            assert dialog.buttonBar.height() == 48
            dialog.grab()
            if action == 'accept':
                dialog.yesButton.click()
            elif action == 'cancel':
                dialog.cancelButton.click()
            else:
                popup.close()
            assert results == ['accepted' if action == 'accept' else 'rejected']
            assert not popup.isVisible()
            QTest.qWait(30)
    owner.close()
    print('PASS: custom content, themes, confirm, cancel and dismissal')


if __name__ == '__main__':
    run()
