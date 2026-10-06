"""Windows live capture integration: sample only a controlled Qt test window's pixels."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'windows')

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import ScreenColorPicker


class TestSurface(QWidget):
    def __init__(self):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.color = QColor('#20C040')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color)


def run():
    if sys.platform != 'win32' or sys.getwindowsversion().build < 19041:
        print('SKIP: live capture needs Windows 10 2004+')
        return
    import ctypes
    from ctypes.wintypes import BOOL, DWORD, HWND

    app = QApplication([])
    if app.platformName() != 'windows':
        print('SKIP: native Windows Qt backend required')
        return
    screen = app.primaryScreen()
    surface = TestSurface()
    origin = screen.availableGeometry().topLeft() + QPoint(100, 100)
    surface.setGeometry(QRect(origin, QPoint(origin.x() + 239, origin.y() + 179)))
    picker = ScreenColorPicker(parent=surface)
    picker.resize(picker.sizeHint())
    picker.setFreezeScreenEnabled(False)
    # All samples are inside this visible, topmost test surface, away from its button.
    position = origin + QPoint(110, 90)
    fixture = QImage(1, 1, QImage.Format_ARGB32)
    fixture.fill(Qt.black)
    errors, picked = [], []
    picker.errorOccurred.connect(errors.append)
    picker.colorPicked.connect(picked.append)
    surface.show()
    surface.raise_()
    surface.activateWindow()
    QTest.qWait(200)
    QTimer.singleShot(10000, picker.cancelPicking)  # Defensive input-overlay deadline.
    try:
        with patch.object(picker, '_captureScreens', return_value=[(screen, screen.geometry(), fixture)]), \
                patch.object(QCursor, 'pos', return_value=position):
            assert picker.startPicking(), errors
            QTest.qWait(150)
            assert picker.isPicking(), errors
            affinity = DWORD()
            getAffinity = ctypes.WinDLL('user32').GetWindowDisplayAffinity
            getAffinity.argtypes = (HWND, ctypes.POINTER(DWORD))
            getAffinity.restype = BOOL
            assert getAffinity(HWND(int(picker._overlays[0].winId())), ctypes.byref(affinity))
            assert affinity.value == 0x11
            assert picker._hoverColor == surface.color, (picker._hoverColor.name(), surface.color.name())
            original = picker.color()
            # The test window continues repainting under the transparent overlay.
            # Keep the pointer stationary and verify a new live pixel is sampled.
            surface.color = QColor('#8040C0')
            surface.update()
            QTest.qWait(180)
            assert picker.isPicking() and not errors
            assert picker._hoverColor == surface.color, (picker._hoverColor.name(), surface.color.name())
            assert picker.color() == original  # preview is not a commit
            picker._confirmAt(position)
            assert picker.color() == surface.color and len(picked) == 1
            assert not picker.isPicking() and not picker._overlays and not picker._timer.isActive()
    finally:
        picker.cancelPicking()
        surface.close()
        QApplication.processEvents()
    print('PASS: native Windows capture exclusion, live Qt repaint, stationary-pointer refresh and confirmation; '
          'only controlled test-window pixels sampled, no desktop screenshot saved')


if __name__ == '__main__':
    run()
