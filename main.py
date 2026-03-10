from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import (
    FilledPushButton,
    FluentIcon,
    FluentTranslator,
    OutlinedPushButton,
    PushButton,
    RangeSlider,  # noqa
    RoundPushButton,
    RoundToolButton,
    Tag,
    ToolTipSlider,  # noqa
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

        # 切换主题
        self.theme_button = PushButton("切换主题")
        layout.addWidget(self.theme_button)
        self.theme_button.clicked.connect(toggleTheme)

        layout.addStretch()
        return page


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    translator = FluentTranslator()
    app.installTranslator(translator)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
