"""Capture a shortcut, then register it explicitly in the demo only."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import BodyLabel, CheckBox, PushButton, ShortcutPicker


class ShortcutPickerDemo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(12)
        layout.addWidget(BodyLabel('ShortcutPicker — 快捷键选择器', self))
        hint = BodyLabel('点击整个卡片录制组合键，保存后生效；重置恢复 Ctrl+Shift+A，取消保留原快捷键。', self)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.picker = ShortcutPicker('Ctrl+Shift+A', self)
        self.picker.setDialogTitle('激活快捷键')
        self.picker.setDialogDescription('按下组合键以更改此快捷键')
        controls = QHBoxLayout()
        controls.addWidget(self.picker)
        self.clearButton = PushButton('清空', self)
        controls.addWidget(self.clearButton)
        controls.addStretch()
        layout.addLayout(controls)
        self.captureEscape = CheckBox('允许录制 Esc（勾选后需点击取消按钮退出）', self)
        self.captureEscape.toggled.connect(lambda enabled: self.picker.setEscapeCancelsCapture(not enabled))
        layout.addWidget(self.captureEscape)
        self.sequenceLabel = BodyLabel(self)
        self.sequenceLabel.setWordWrap(True)
        layout.addWidget(self.sequenceLabel)
        self.triggerLabel = BodyLabel('保存后，在本窗口按下该快捷键即可测试（系统保留组合键可能无法捕获）。', self)
        self.triggerLabel.setWordWrap(True)
        layout.addWidget(self.triggerLabel)
        self.shortcut = QShortcut(self.picker.keySequence(), self)
        self.shortcut.setContext(Qt.WindowShortcut)
        self.shortcut.activated.connect(self._triggered)
        self.picker.keySequenceChanged.connect(self._changed)
        self.clearButton.clicked.connect(self.picker.clear)
        self._changed(self.picker.keySequence())

    def _changed(self, sequence):
        self.shortcut.setKey(sequence)
        self.sequenceLabel.setText('当前快捷键：' + (sequence.toString(QKeySequence.NativeText) or '未设置'))

    def _triggered(self):
        self.triggerLabel.setText('已触发：' + self.picker.keySequence().toString(QKeySequence.NativeText))
