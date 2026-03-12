from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from gallery.view.chart.home_interface import ChartMainWindow  # noqa
from qfluentwidgets_pro import (
    DropMultiFilesWidget,
    DropSingleFileWidget,
    FilledPushButton,
    FluentIcon,
    FluentTranslator,
    LabelLineEdit,
    OutlinedPushButton,
    PinBox,
    PushButton,
    RoundPushButton,
    RoundToolButton,
    Splitter,
    StepProgressBar,
    Tag,
    TopFluentWindow,
    TopNavigationItemPosition,
    toggleTheme,
)


class MainWindow(TopFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TopFluentWindow Demo")
        self.resize(900, 600)

        # create sub interfaces
        self.homeInterface = self._createHomePage()
        self.homeInterface.setObjectName("homeInterface")
        self.addSubInterface(
            self.homeInterface,
            FluentIcon.HOME,
            "Home",
            TopNavigationItemPosition.LEFT,
            expanded=True,  # show both icon and text for Home
        )

        self.buttonsInterface = self._createButtonsPage()
        self.buttonsInterface.setObjectName("buttonsInterface")
        self.addSubInterface(
            self.buttonsInterface,
            FluentIcon.ACCEPT,
            "Buttons",
            TopNavigationItemPosition.LEFT,
        )

        self.settingsInterface = QWidget(self)
        self.settingsInterface.setObjectName("settingsInterface")
        layout = QVBoxLayout(self.settingsInterface)
        layout.addWidget(PushButton("Settings Page"))
        self.addSubInterface(
            self.settingsInterface,
            FluentIcon.SETTING,
            "Settings",
            TopNavigationItemPosition.RIGHT,
        )

        self.dropInterface = self._createDropPage()
        self.dropInterface.setObjectName("dropInterface")
        self.addSubInterface(
            self.dropInterface,
            FluentIcon.FOLDER,
            "Drop Files",
            TopNavigationItemPosition.LEFT,
        )

        self.splitterInterface = self._createSplitterPage()
        self.splitterInterface.setObjectName("splitterInterface")
        self.addSubInterface(
            self.splitterInterface,
            FluentIcon.TILES,
            "Splitter",
            TopNavigationItemPosition.LEFT,
        )

    def _createHomePage(self):
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.addWidget(PushButton("Welcome to TopFluentWindow!"))
        return page

    def _createButtonsPage(self):
        page = QWidget(self)
        layout = QVBoxLayout(page)

        # RoundPushButton test
        self.roundbtn = RoundPushButton("RoundPushButton")
        layout.addWidget(self.roundbtn)

        # RoundToolButton test
        hLayout = QHBoxLayout()
        layout.addLayout(hLayout)

        self.roundToolBtn = RoundToolButton(FluentIcon.ADD)
        self.roundToolBtn.setFixedSize(40, 40)
        hLayout.addWidget(self.roundToolBtn)

        self.roundToolBtn2 = RoundToolButton(FluentIcon.SETTING)
        self.roundToolBtn2.setFixedSize(32, 32)
        hLayout.addWidget(self.roundToolBtn2)

        # OutlinedPushButton test
        hLayout2 = QHBoxLayout()
        layout.addLayout(hLayout2)

        self.outlinedBtn = OutlinedPushButton("Outlined")
        hLayout2.addWidget(self.outlinedBtn)

        self.outlinedBtn2 = OutlinedPushButton(FluentIcon.ADD, "With Icon")
        hLayout2.addWidget(self.outlinedBtn2)

        # FilledPushButton test - 5 color schemes
        hLayout4 = QHBoxLayout()
        layout.addLayout(hLayout4)

        self.filledInfo = FilledPushButton("Information")
        self.filledInfo.setColorScheme(FilledPushButton.INFORMATION)
        hLayout4.addWidget(self.filledInfo)

        self.filledSuccess = FilledPushButton(FluentIcon.GITHUB, "Success")
        self.filledSuccess.setColorScheme(FilledPushButton.SUCCESS)
        hLayout4.addWidget(self.filledSuccess)

        self.filledAttention = FilledPushButton("Attention")
        self.filledAttention.setColorScheme(FilledPushButton.ATTENTION)
        hLayout4.addWidget(self.filledAttention)

        # Tag examples
        hLayout7 = QHBoxLayout()
        layout.addLayout(hLayout7)

        self.tagInfo = Tag("Information")
        self.tagInfo.setIcon(FluentIcon.INFO)
        self.tagInfo.setType(Tag.INFORMATION)
        hLayout7.addWidget(self.tagInfo)

        self.tagSuccess = Tag("Success")
        self.tagSuccess.setIcon(FluentIcon.ACCEPT)
        self.tagSuccess.setType(Tag.SUCCESS)
        hLayout7.addWidget(self.tagSuccess)

        self.tagWarning = Tag("Warning")
        self.tagWarning.setIcon(FluentIcon.EDIT)
        self.tagWarning.setType(Tag.WARNING)
        hLayout7.addWidget(self.tagWarning)

        # PinBox example
        from qfluentwidgets_pro import BodyLabel

        layout.addWidget(BodyLabel("PinBox (验证码输入):"))
        self.pinBox = PinBox()
        self.pinBox.textChanged.connect(lambda pins: print(f"PIN: {''.join(pins)}"))
        layout.addWidget(self.pinBox)

        layout.addWidget(BodyLabel("LabelLineEdit"))
        self.labelLine = LabelLineEdit("a", "b")
        self.labelLine.setPlaceholderText("text")
        layout.addWidget(self.labelLine)

        stepbutton = StepProgressBar(4)
        stepbutton.setIcons(
            [
                FluentIcon.HOME,
                FluentIcon.SEARCH,
                FluentIcon.SETTING,
                FluentIcon.CHECKBOX,
            ]
        )
        stepbutton.setStepNames(["开始", "上传中", "处理", "完成"])
        stepbutton.setNonInteractive(True)
        stepbutton.nextStep()
        layout.addWidget(stepbutton)

        # 切换主题
        self.theme_button = PushButton("切换主题")
        layout.addWidget(self.theme_button)
        self.theme_button.clicked.connect(toggleTheme)

        self.chart_button = PushButton("打开图表窗口")
        layout.addWidget(self.chart_button)
        self.chart_button.clicked.connect(self._openChartWindow)

        layout.addStretch()
        return page

    def _createDropPage(self):
        """Create drop files demo page"""
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # DropSingleFileWidget
        from qfluentwidgets_pro import BodyLabel

        layout.addWidget(BodyLabel("Drop Single File:"))
        self.singleDrop = DropSingleFileWidget()
        self.singleDrop.setFixedHeight(120)
        self.singleDrop.selectionChange.connect(
            lambda path: print(f"Single file: {path}")
        )
        layout.addWidget(self.singleDrop)

        # DropMultiFilesWidget
        layout.addWidget(BodyLabel("Drop Multiple Files:"))
        self.multiDrop = DropMultiFilesWidget()
        self.multiDrop.setFixedHeight(120)
        self.multiDrop.selectionChange.connect(
            lambda paths: print(f"Multiple files: {paths}")
        )
        layout.addWidget(self.multiDrop)

        layout.addStretch()
        return page

    def _createSplitterPage(self):
        """Create splitter demo page"""
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor, QPainter
        from PySide6.QtWidgets import QWidget

        from qfluentwidgets_pro import BodyLabel, isDarkTheme, themeColor

        class BackgroundCard(QWidget):
            def __init__(self, text, parent=None):
                super().__init__(parent)
                self.text = text
                self.setMinimumSize(100, 80)

            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(Qt.NoPen)
                painter.setBrush(themeColor())
                painter.drawRoundedRect(self.rect(), 6, 6)

                painter.setPen(
                    QColor(255, 255, 255) if isDarkTheme() else QColor(0, 0, 0)
                )
                font = self.font()
                font.setPixelSize(16)
                painter.setFont(font)
                painter.drawText(self.rect(), self.text, Qt.AlignCenter)

        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Horizontal splitter
        layout.addWidget(BodyLabel("Horizontal Splitter:"))
        hSplitter = Splitter(Qt.Horizontal)
        hSplitter.addWidget(BackgroundCard("Left", self))
        hSplitter.addWidget(BackgroundCard("Center", self))
        hSplitter.addWidget(BackgroundCard("Right", self))
        hSplitter.setFixedHeight(120)
        layout.addWidget(hSplitter)

        # Vertical splitter
        layout.addWidget(BodyLabel("Vertical Splitter:"))
        vSplitter = Splitter(Qt.Vertical)
        vSplitter.addWidget(BackgroundCard("Top", self))
        vSplitter.addWidget(BackgroundCard("Bottom", self))
        vSplitter.setFixedHeight(250)
        layout.addWidget(vSplitter)

        layout.addStretch()
        return page

    def _openChartWindow(self):
        """Open chart window with mica effect enabled"""
        chart_window = ChartMainWindow()
        chart_window.show()
        chart_window.setMicaEffectEnabled(True)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    translator = FluentTranslator()
    app.installTranslator(translator)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
