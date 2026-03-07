from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import (
    Clip,
    FilledProgressBar,
    FilledPushButton,
    FluentIcon,
    FluentTranslator,
    FluentWidget,
    HyperlinkToolButton,
    LuminaPushButton,
    MultiSegmentProgressRing,
    OutlinedPushButton,
    OutlinedToolButton,
    PushButton,
    RangeSlider,  # noqa
    RoundPushButton,
    RoundToolButton,
    ScrollArea,
    SubtitleCheckBox,
    SubtitleRadioButton,
    Tag,
    TextPushButton,
    ToolTipSlider,  # noqa
    toggleTheme,
    RadialGauge,
    DropMultiFilesWidget,
    DropSingleFileWidget
)


class MainWindow(FluentWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")
        self.resize(800, 800)

        self.scrollArea = ScrollArea(self)
        self.scrollArea.enableTransparentBackground()
        self.scrollArea.setWidgetResizable(True)

        self.contentWidget = QWidget(self.scrollArea)
        self.contentWidget.setStyleSheet("background: transparent;")
        self.view = QVBoxLayout(self.contentWidget)
        self.contentWidget.setLayout(self.view)
        self.scrollArea.setWidget(self.contentWidget)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.scrollArea)
        self.setLayout(self.mainLayout)

        self.pushbtn = FilledProgressBar()
        self.pushbtn.setIcon(FluentIcon.ACCEPT)
        self.pushbtn.setValue(50)
        self.view.addWidget(self.pushbtn)

        self.roundbtn = RoundPushButton("RoundPushButton")
        self.roundbtn.clicked.connect(lambda: self.pushbtn.setValue(self.pushbtn.value() + 10))
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

        ringLayout = QHBoxLayout()
        self.view.addLayout(ringLayout)

        self.ring1 = MultiSegmentProgressRing()
        self.ring1.setText("75%")
        self.ring1.setFixedSize(100, 100)
        self.ring1.setStrokeWidth(8)
        self.ring1.setGapDegree(4)
        self.ring1.setSegments(
            [
                (0.4, QColor("#22c55e")),
                (0.3, QColor("#3b82f6")),
                (0.2, QColor("#f59e0b")),
                (0.1, QColor("#ef4444")),
            ]
        )
        ringLayout.addWidget(self.ring1)

        self.ring2 = RadialGauge()
        self.ring2.setValue(50)
        ringLayout.addWidget(self.ring2)

        self.selectFile1 = DropSingleFileWidget()
        self.selectFile2 = DropMultiFilesWidget()
        self.view.addWidget(self.selectFile1)
        self.view.addWidget(self.selectFile2)

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
