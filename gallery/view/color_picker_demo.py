"""Lightweight color component examples with editable palettes."""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import BodyLabel, CheckBox, CircleColorPicker, DropDownColorPalette, DropDownColorPicker, LineEdit, PushButton, ScreenColorPicker, ScrollArea, toggleTheme


class ColorPickerDemo(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('colorPickerInterface')
        content = QWidget(self)
        layout = QVBoxLayout(content)
        self.setWidget(content)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(BodyLabel('CircleColorPicker — 自定义圆形色板'))
        layout.addWidget(BodyLabel('点击选择颜色；方向键切换，Home / End 跳转。'))
        self.picker = CircleColorPicker(self)
        self.picker.setCurrentIndex(1)
        layout.addWidget(self.picker)
        self.colorLabel = BodyLabel(self)
        self.picker.colorChanged.connect(self._showColor)
        self._showColor(self.picker.color())
        layout.addWidget(self.colorLabel)
        paletteHint = BodyLabel('用逗号分隔颜色，点击“应用色板”替换；例如 #FF4343, #FFB900, #107C10。')
        paletteHint.setWordWrap(True)
        layout.addWidget(paletteHint)
        controls = QHBoxLayout()
        self.paletteEdit = LineEdit(self)
        self.paletteEdit.setText(', '.join(CircleColorPicker.DEFAULT_COLORS))
        apply = PushButton('应用色板', self)
        reset = PushButton('恢复示例', self)
        theme = PushButton('切换主题', self)
        controls.addWidget(self.paletteEdit, 1)
        for widget in (apply, reset, theme):
            controls.addWidget(widget)
        layout.addLayout(controls)
        self.messageLabel = BodyLabel(self)
        self.messageLabel.setWordWrap(True)
        layout.addWidget(self.messageLabel)
        apply.clicked.connect(self._applyPalette)
        self.paletteEdit.returnPressed.connect(self._applyPalette)
        reset.clicked.connect(self._resetPalette)
        theme.clicked.connect(toggleTheme)
        layout.addSpacing(12)
        layout.addWidget(BodyLabel('ScreenColorPicker — 屏幕取色'))
        screenHint = BodyLabel('点击滴管后移动鼠标预览，左键确认；Esc 或右键取消。可切换冻结 / 实时取色。')
        screenHint.setWordWrap(True)
        layout.addWidget(screenHint)
        self.screenPicker = ScreenColorPicker('#0078D4', self)
        self.freezeScreenCheckBox = CheckBox('取色时冻结屏幕', self)
        self.freezeScreenCheckBox.setChecked(self.screenPicker.isFreezeScreenEnabled())
        self.freezeScreenCheckBox.toggled.connect(self.screenPicker.setFreezeScreenEnabled)
        layout.addWidget(self.freezeScreenCheckBox)
        layout.addWidget(self.screenPicker)
        self.screenColorLabel = BodyLabel('当前颜色：#0078d4', self)
        layout.addWidget(self.screenColorLabel)
        self.screenMessageLabel = BodyLabel(self)
        self.screenMessageLabel.setWordWrap(True)
        layout.addWidget(self.screenMessageLabel)
        self.screenPicker.colorChanged.connect(lambda color: self.screenColorLabel.setText('当前颜色：' + color.name()))
        self.screenPicker.colorPicked.connect(lambda color: self.screenMessageLabel.setText('已选取 ' + color.name()))
        self.screenPicker.pickingCanceled.connect(lambda: self.screenMessageLabel.setText('已取消，原颜色保持不变。'))
        self.screenPicker.errorOccurred.connect(self.screenMessageLabel.setText)
        layout.addSpacing(12)
        layout.addWidget(BodyLabel('DropDownColorPalette — 下拉调色盘'))
        paletteHint = BodyLabel('选择主题色或标准色；“More Colors...” 打开颜色对话框，取消保留原色。')
        paletteHint.setWordWrap(True)
        layout.addWidget(paletteHint)
        self.dropDownPalette = DropDownColorPalette('#0078D4', self)
        layout.addWidget(self.dropDownPalette)
        self.dropDownColorLabel = BodyLabel('当前颜色：#0078d4', self)
        layout.addWidget(self.dropDownColorLabel)
        self.dropDownPalette.colorChanged.connect(
            lambda color: self.dropDownColorLabel.setText('当前颜色：' + color.name()))
        layout.addSpacing(12)
        layout.addWidget(BodyLabel('DropDownColorPicker — 下拉颜色编辑器'))
        pickerHint = BodyLabel('拖动色板、滑条或编辑数值；可切换 RGB / HSV。勾号确认，叉号 / Esc / 外部点击取消。')
        pickerHint.setWordWrap(True)
        layout.addWidget(pickerHint)
        self.dropDownPicker = DropDownColorPicker('#0078D4', self)
        layout.addWidget(self.dropDownPicker)
        self.alphaCheckBox = CheckBox('允许调整透明度', self)
        self.alphaCheckBox.setChecked(self.dropDownPicker.isAlphaEnabled())
        self.alphaCheckBox.toggled.connect(self.dropDownPicker.setAlphaEnabled)
        layout.addWidget(self.alphaCheckBox)
        self.dropDownPickerLabel = BodyLabel('当前颜色：#ff0078d4', self)
        layout.addWidget(self.dropDownPickerLabel)
        self.dropDownPicker.colorChanged.connect(
            lambda color: self.dropDownPickerLabel.setText('当前颜色：' + color.name(QColor.HexArgb)))
        layout.addStretch()

    def _showColor(self, color):
        text = color.name(QColor.HexArgb if color.alpha() < 255 else QColor.HexRgb) if color.isValid() else '未选择'
        self.colorLabel.setText('当前颜色：' + text)

    def _applyPalette(self):
        text = self.paletteEdit.text().strip()
        try:
            self.picker.setColors([part.strip() for part in text.split(',')] if text else [])
        except (TypeError, ValueError):
            self.messageLabel.setText('颜色格式无效；原色板保持不变。请使用 #RRGGBB 或 #AARRGGBB。')
            return
        self.messageLabel.setText('色板已更新。')

    def _resetPalette(self):
        self.paletteEdit.setText(', '.join(CircleColorPicker.DEFAULT_COLORS))
        self.picker.setColors(CircleColorPicker.DEFAULT_COLORS)
        self.picker.setCurrentIndex(1)
        self.messageLabel.setText('已恢复示例色板。')
