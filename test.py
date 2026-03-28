import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout
from qfluentwidgets import EditableComboBox, FluentWindow
from qfluentwidgets import FluentIcon as FIF


class Widget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.editcombox = EditableComboBox()
        list1 = [str(a) for a in range(20)]
        self.editcombox.addItems(list1)
        self.hBoxLayout.addWidget(self.editcombox)
        self.hBoxLayout.addWidget(self.editcombox, 1, Qt.AlignCenter)

        # 必须给子界面设置全局唯一的对象名
        self.setObjectName(text.replace(" ", "-"))


class Window(FluentWindow):
    """主界面"""

    def __init__(self):
        super().__init__()

        self.homeInterface = Widget("Home Interface", self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, "Home")

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(":/qfluentwidgets/images/logo.png"))
        self.setWindowTitle("PyQt-Fluent-Widgets")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
