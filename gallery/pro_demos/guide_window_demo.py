"""Pages are regular widgets; nothing in GuideWindow assumes a form or image."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from qfluentwidgets_pro import BodyLabel, CaptionLabel, GuideWindow, LineEdit, TitleLabel


class GuideWindowDemo(GuideWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('GuideWindow — 分步向导')
        welcome = QWidget()
        welcomeLayout = QVBoxLayout(welcome)
        welcomeLayout.setContentsMargins(64, 40, 64, 40)
        welcomeLayout.addStretch()
        welcomeLayout.addWidget(TitleLabel('欢迎使用分步向导', welcome))
        description = BodyLabel('每一步都是使用者提供的 QWidget，可以放图片、输入框或任意自定义组件。', welcome)
        description.setWordWrap(True)
        welcomeLayout.addWidget(description)
        welcomeLayout.addStretch()
        self.addPage(welcome)

        config = QWidget()
        columns = QHBoxLayout(config)
        columns.setContentsMargins(72, 0, 64, 36)
        columns.setSpacing(56)
        illustration = QLabel('\U0001f917', config)
        illustration.setFont(QFont('Segoe UI Emoji', 108))
        illustration.setFixedWidth(176)
        illustration.setAlignment(Qt.AlignCenter)
        columns.addWidget(illustration)
        form = QVBoxLayout()
        form.setSpacing(12)
        form.addStretch()
        title = TitleLabel('Hugging Face 配置', config)
        form.addWidget(title)
        form.addSpacing(2)
        form.addWidget(CaptionLabel('访问令牌', config))
        self.tokenEdit = LineEdit(config)
        self.tokenEdit.setPlaceholderText('请输入访问令牌')
        # The demo neither sends nor persists this text; hide typed credentials.
        self.tokenEdit.setEchoMode(LineEdit.EchoMode.Password)
        form.addWidget(self.tokenEdit)
        form.addSpacing(10)
        form.addWidget(BodyLabel('代理服务器', config))
        self.proxyEdit = LineEdit(config)
        self.proxyEdit.setPlaceholderText('请输入代理服务器地址')
        form.addWidget(self.proxyEdit)
        form.addStretch()
        columns.addLayout(form, 1)
        self.addPage(config)

        summary = QWidget()
        summaryLayout = QVBoxLayout(summary)
        summaryLayout.setContentsMargins(64, 40, 64, 40)
        summaryLayout.addStretch()
        summaryLayout.addWidget(TitleLabel('准备就绪', summary))
        hint = BodyLabel('点击完成结束向导。示例仅展示页面导航，不保存设置、不连接 Hugging Face。', summary)
        hint.setWordWrap(True)
        summaryLayout.addWidget(hint)
        summaryLayout.addStretch()
        self.addPage(summary)
        # Start on the reference form page so both navigation buttons are visible.
        self.setCurrentIndex(1)
        self.previousButton.setText('上一步')
        self.currentIndexChanged.connect(self._updateChineseLabels)
        self._updateChineseLabels()

    def _updateChineseLabels(self, *args):
        self.nextButton.setText('完成' if self.currentIndex() == self.count() - 1 else '下一步')
