from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets_pro import (
    Clip,
    FilledPushButton,
    FluentIcon,
    FluentTranslator,
    FluentWidget,
    HyperlinkToolButton,
    LuminaPushButton,
    OutlinedPushButton,
    OutlinedToolButton,
    PushButton,
    RangeSlider,  # noqa
    RoundPushButton,
    RoundToolButton,
    SubtitleCheckBox,
    SubtitleRadioButton,
    Tag,
    TextPushButton,
    ToolTipSlider,  # noqa
    toggleTheme,
)


class MainWindow(FluentWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")
        self.resize(800, 800)

        self.view = QVBoxLayout()
        self.setLayout(self.view)

        self.pushbtn = RangeSlider()
        self.view.addWidget(self.pushbtn)

        self.roundbtn = RoundPushButton("RoundPushButton")
        self.view.addWidget(self.roundbtn)

        # RoundToolButton test
        hLayout = QHBoxLayout()
        self.view.addLayout(hLayout)

        self.roundToolBtn = RoundToolButton(FluentIcon.ADD)
        self.roundToolBtn.setFixedSize(40, 40)
        hLayout.addWidget(self.roundToolBtn)

        self.roundToolBtn2 = RoundToolButton(FluentIcon.SETTING)
        self.roundToolBtn2.setFixedSize(32, 32)
        hLayout.addWidget(self.roundToolBtn2)

        # OutlinedPushButton test
        hLayout2 = QHBoxLayout()
        self.view.addLayout(hLayout2)

        self.outlinedBtn = OutlinedPushButton("Outlined")
        hLayout2.addWidget(self.outlinedBtn)

        self.outlinedBtn2 = OutlinedPushButton(FluentIcon.ADD, "With Icon")
        hLayout2.addWidget(self.outlinedBtn2)

        # OutlinedToolButton test
        hLayout3 = QHBoxLayout()
        self.view.addLayout(hLayout3)

        self.outlinedToolBtn = OutlinedToolButton(FluentIcon.SETTING)
        self.outlinedToolBtn.setFixedSize(40, 40)
        hLayout3.addWidget(self.outlinedToolBtn)

        self.outlinedToolBtn2 = OutlinedToolButton(FluentIcon.SEARCH)
        self.outlinedToolBtn2.setFixedSize(32, 32)
        hLayout3.addWidget(self.outlinedToolBtn2)

        # FilledPushButton test - 5 color schemes
        hLayout4 = QHBoxLayout()
        self.view.addLayout(hLayout4)

        self.filledInfo = FilledPushButton("Information")
        self.filledInfo.setColorScheme(FilledPushButton.INFORMATION)
        hLayout4.addWidget(self.filledInfo)

        self.filledSuccess = FilledPushButton(FluentIcon.GITHUB, "Success")
        self.filledSuccess.setColorScheme(FilledPushButton.SUCCESS)
        hLayout4.addWidget(self.filledSuccess)

        self.filledAttention = FilledPushButton("Attention")
        self.filledAttention.setColorScheme(FilledPushButton.ATTENTION)
        hLayout4.addWidget(self.filledAttention)

        self.filledWarning = FilledPushButton("Warning")
        self.filledWarning.setColorScheme(FilledPushButton.WARNING)
        hLayout4.addWidget(self.filledWarning)

        self.filledError = FilledPushButton("Error")
        self.filledError.setColorScheme(FilledPushButton.ERROR)
        hLayout4.addWidget(self.filledError)

        # TextPushButton test - 5 color schemes
        hLayout5 = QHBoxLayout()
        self.view.addLayout(hLayout5)

        self.textInfo = HyperlinkToolButton(FluentIcon.LINK, "https://github.com")
        hLayout5.addWidget(self.textInfo)

        self.textSuccess = TextPushButton(FluentIcon.GITHUB, "Success")
        self.textSuccess.setColorScheme(TextPushButton.SUCCESS)
        hLayout5.addWidget(self.textSuccess)

        self.textAttention = TextPushButton("Attention")
        self.textAttention.setColorScheme(TextPushButton.ATTENTION)
        hLayout5.addWidget(self.textAttention)

        self.textWarning = TextPushButton("Warning")
        self.textWarning.setColorScheme(TextPushButton.WARNING)
        hLayout5.addWidget(self.textWarning)

        self.textError = TextPushButton("Error")
        self.textError.setColorScheme(TextPushButton.ERROR)
        hLayout5.addWidget(self.textError)

        # LuminaPushButton test
        hLayout6 = QHBoxLayout()
        self.view.addLayout(hLayout6)

        self.luminaBtn1 = LuminaPushButton("Lumina Button")
        self.luminaBtn1.setGlowColor(QColor(255, 100, 50))
        hLayout6.addWidget(self.luminaBtn1)

        self.luminaBtn2 = LuminaPushButton(FluentIcon.GITHUB, "With Icon")
        self.luminaBtn2.setDisabled(True)
        hLayout6.addWidget(self.luminaBtn2)

        clip = Clip("text")
        clip.setIcon(FluentIcon.ACCEPT)
        self.view.addWidget(clip)

        # Tag examples
        hLayout7 = QHBoxLayout()
        self.view.addLayout(hLayout7)

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

        self.tagError = Tag("Error")
        self.tagError.setIcon(FluentIcon.CLOSE)
        self.tagError.setType(Tag.ERROR)
        hLayout7.addWidget(self.tagError)

        self.tagProgress = Tag("Progress")
        self.tagProgress.setIcon(FluentIcon.SYNC)
        self.tagProgress.setType(Tag.PROGRESS)
        hLayout7.addWidget(self.tagProgress)

        subraido1 = SubtitleRadioButton("SubtitleRadioButton", "subtitle")
        self.view.addWidget(subraido1)

        subcheck = SubtitleCheckBox("SubtitleCheckBox", "Subtitle")
        self.view.addWidget(subcheck)

        # 切换主题
        self.theme_button = PushButton("切换主题")
        self.view.addWidget(self.theme_button)
        self.theme_button.clicked.connect(toggleTheme)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    translator = FluentTranslator()
    app.installTranslator(translator)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
