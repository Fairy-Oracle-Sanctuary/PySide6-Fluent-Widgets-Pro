"""Run with py -3.9 tests/check_avatar_picker.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import AvatarPicker, ImageCropper, CropShape


def run():
    app = QApplication([])
    owner = QWidget()
    owner.resize(800, 600)
    image = QImage(400, 200, QImage.Format_RGB32)
    image.fill(Qt.red)
    avatar = AvatarPicker(image, owner)
    avatar.setRadius(48)
    owner.show()
    app.processEvents()
    avatar._hovered = True
    assert not avatar.grab().isNull()
    changed = []
    avatar.imageChanged.connect(changed.append)
    def finish(accept):
        editor = owner.findChild(ImageCropper)
        assert editor and editor.canvas.shape == CropShape.CIRCLE
        assert editor.canvas.selection.width() == editor.canvas.selection.height()
        if accept:
            editor.accept()
        else:
            editor.reject()
    QTimer.singleShot(30, lambda: finish(True))
    avatar.cropImage(image)
    assert len(changed) == 1 and avatar.image.width() == avatar.image.height()
    assert avatar.width() == 96 and avatar.height() == 96
    app.processEvents()
    QTimer.singleShot(30, lambda: finish(False))
    avatar.cropImage(image)
    assert len(changed) == 1
    owner.close()
    print('PASS: hover paint, circular shared editor, confirm, cancel and radius')


if __name__ == '__main__':
    run()
