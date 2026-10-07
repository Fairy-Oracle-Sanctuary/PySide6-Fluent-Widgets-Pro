"""A compact action-backed menu bar; commands update demo feedback only."""

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QVBoxLayout, QWidget

from qfluentwidgets_pro import BodyLabel, MenuBar, RoundMenu


class MenuBarDemo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(10)
        layout.addWidget(BodyLabel('MenuBar — 顶部菜单导航', self))
        self.menuBar = MenuBar(self)
        layout.addWidget(self.menuBar)
        fileMenu = self.menuBar.addMenu('文件(&F)')
        self.openAction = QAction('打开文件...', self, shortcut='Ctrl+O')
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(QAction('打开文件夹...', self))
        fileMenu.addSeparator()
        fileMenu.addActions([QAction('新建文件...', self), QAction('新建文本文件', self)])
        editMenu = self.menuBar.addMenu('编辑(&E)')
        undo = QAction('撤销', self)
        undo.setEnabled(False)
        editMenu.addAction(undo)
        editMenu.addAction(QAction('复制', self))
        editMenu.addAction(QAction('粘贴', self))
        self.menuBar.addMenu('选择(&S)').addAction(QAction('全选', self))
        viewMenu = self.menuBar.addMenu('查看(&V)')
        viewMenu.addAction(QAction('显示状态栏', self, checkable=True, checked=True))
        zoom = RoundMenu('缩放', viewMenu)
        zoom.addActions([QAction('放大', self), QAction('缩小', self), QAction('恢复缩放', self)])
        viewMenu.addMenu(zoom)
        self.menuBar.addMenu('转到(&G)').addAction(QAction('转到行...', self))
        self.statusLabel = BodyLabel('点击标题打开；移到其他标题切换。Alt+字母 / F10 可用键盘导航。', self)
        self.statusLabel.setWordWrap(True)
        layout.addWidget(self.statusLabel)
        self.menuBar.triggered.connect(self._triggered)

    def _triggered(self, action):
        suffix = ('（已勾选）' if action.isChecked() else '（已取消勾选）') if action.isCheckable() else ''
        self.statusLabel.setText('已触发：' + action.text() + suffix + '（仅演示，不操作文件）')
