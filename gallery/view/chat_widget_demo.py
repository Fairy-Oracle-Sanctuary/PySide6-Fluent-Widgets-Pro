"""Native QQ-style chat demo; streaming is simulated, with no model/API key."""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import BodyLabel, CheckBox, FluentIcon, PushButton, toggleTheme
from qfluentwidgets_pro.components.widgets.chat_widget import ChatWidget


class ChatWidgetDemo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('chatWidgetInterface')
        self._streamId = None
        self._chunks = []
        self.timer = QTimer(self)
        self.timer.setInterval(35)
        self.timer.timeout.connect(self._tick)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        header = QHBoxLayout()
        header.addWidget(BodyLabel('ChatWidget — 原生聊天组件', self))
        header.addStretch()
        self.messageToolsCheckBox = CheckBox('消息工具栏', self)
        self.messageToolsCheckBox.setChecked(True)
        header.addWidget(self.messageToolsCheckBox)
        reset = PushButton('重置示例', self)
        reset.clicked.connect(self._reset)
        header.addWidget(reset)
        theme = PushButton('切换主题', self)
        theme.clicked.connect(toggleTheme)
        header.addWidget(theme)
        layout.addLayout(header)
        self.chat = ChatWidget(self)
        self.chat.setMessageToolBarEnabled(True)
        self.messageToolsCheckBox.toggled.connect(self.chat.setMessageToolBarEnabled)
        layout.addWidget(self.chat, 1)
        self.status = BodyLabel('本地演示，不调用模型接口。', self)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.chat.addToolButton(FluentIcon.EMOJI_TAB_SYMBOLS, '表情',
                                lambda: self.chat.inputEdit.insertPlainText(' 😊 '))
        self.chat.addToolButton(FluentIcon.FOLDER, '文件（自定义回调）',
                                lambda: self.status.setText('文件按钮：在这里接入你自己的文件选择与上传逻辑。'))
        self.chat.addToolButton(FluentIcon.PHOTO, '发送本地图片', self._chooseImage)
        self.chat.addToolButton(FluentIcon.MICROPHONE, '语音（自定义回调）',
                                lambda: self.status.setText('语音按钮：在这里接入你自己的录音逻辑。'))
        self.chat.addToolButton(FluentIcon.HISTORY, '跳到最新', self.chat.scrollToBottom, side='right')
        self.chat.addToolButton(FluentIcon.DELETE, '清空消息', self._clear, side='right')
        self.chat.sendRequested.connect(self._send)
        self.chat.stopRequested.connect(self._stop)
        self.chat.renderWarning.connect(self.status.setText)
        self.chat.linkClicked.connect(lambda url: self.status.setText('链接点击（未自动打开）：' + url.toString()))
        self.chat.imageClicked.connect(lambda messageId: self.status.setText('图片点击：' + messageId))
        self.chat.messageActionTriggered.connect(self._messageAction)
        self._reset()

    def _messageAction(self, actionId, messageId):
        labels = {'copy': '复制', 'retry': '重试', 'like': '点赞', 'dislike': '点踩',
                  'readAloud': '朗读', 'share': '分享'}
        self.status.setText(f'消息操作：{labels.get(actionId, actionId)}；消息 ID：{messageId}。'
                            + ('已复制到剪贴板。' if actionId == 'copy' else '此处接入应用自己的处理逻辑。'))

    def _reset(self):
        self._clear()
        self.chat.addMessage('你好！可以发段 Python 示例吗？', role='user', name='我')
        self.chat.addMessage('当然。这是 **原生 Qt** 渲染，不需要 WebView。\n\n'
                             '```python\nname = "Fluent"\nprint(f"Hello, {name}!")\n```\n\n'
                             '公式也可以显示：$E=mc^2$。\n\n'
                             '$$\\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$$', name='Fluent 助手')
        self.chat.addMessage('支持多人聊天、图片和自定义卡片吗？', role='user', name='我')
        self.chat.addMessage('可以，头像和昵称由调用方传入；图片和卡片使用独立消息接口。', name='小伙伴')
        self.chat.addImageMessage(self._sampleImage(), name='小伙伴')
        self.chat.addMessage('输入一句话试试流式输出，工具栏左右两侧的按钮都可以替换。', name='Fluent 助手')

    @staticmethod
    def _sampleImage():
        image = QImage(360, 130, QImage.Format_ARGB32)
        image.fill(QColor('#dff3ff'))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('#55b8ed'))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(28, 28, 74, 74)
        painter.setPen(QColor('#16354a'))
        font = painter.font()
        font.setPixelSize(24)
        painter.setFont(font)
        painter.drawText(120, 0, 225, 130, Qt.AlignVCenter, 'Native Qt chat')
        painter.end()
        return image

    def _chooseImage(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择图片', '', 'Images (*.png *.jpg *.jpeg *.webp *.bmp)')
        if path:
            try:
                self.chat.addImageMessage(path, role='user', name='我')
                self.chat.scrollToBottom()
            except ValueError:
                self.status.setText('无法加载图片。')

    def _send(self, text):
        self.chat.addMessage(text, role='user', name='我')
        self._streamId = self.chat.addMessage('', name='Fluent 助手', streaming=True)
        answer = ('收到。这是本地模拟的流式回复，不会把你的消息发送到网络。\n\n'
                  '**功能展示**\n\n- Markdown 排版\n- 原生代码高亮与复制\n- 自动跟随最新消息，向上滚动后不会抢回位置\n\n'
                  '```python\nmessage_id = chat.addMessage("", name="Assistant", streaming=True)\n'
                  'chat.appendText(message_id, "Hello")\nchat.finishMessage(message_id)\n```\n\n'
                  '公式示例：$\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}$。')
        self._chunks = [answer[i:i + 4] for i in range(0, len(answer), 4)]
        self.chat.setBusy(True)
        self.chat.scrollToBottom()
        self.timer.start()

    def _tick(self):
        if not self._chunks:
            self._stop()
            return
        self.chat.appendText(self._streamId, self._chunks.pop(0))

    def _stop(self):
        self.timer.stop()
        if self._streamId is not None:
            self.chat.finishMessage(self._streamId)
            self._streamId = None
        self._chunks.clear()
        self.chat.setBusy(False)

    def _clear(self):
        self._stop()
        self.chat.clear()
