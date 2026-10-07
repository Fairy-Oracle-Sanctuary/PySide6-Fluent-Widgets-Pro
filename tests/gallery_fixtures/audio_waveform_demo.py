"""File waveform gallery: explicitly opt into decoding and actual audio playback."""
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets_pro import AudioWaveformWidget, BodyLabel, PushButton, toggleTheme
from qfluentwidgets_pro.common.audio_decoder import AudioDecoder


SAMPLE_WAV = Path(__file__).resolve().parents[2] / 'gallery/resource/audio/waveform_sample.wav'


class AudioWaveformDemo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('audioWaveformInterface')
        self._loaded = False
        self._source = QUrl()
        self._message = '请选择音频文件，或加载测试 WAV。'
        self.decoder = AudioDecoder(self)
        self.audioOutput = QAudioOutput(self)
        self.audioOutput.setVolume(.35)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audioOutput)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(BodyLabel('AudioWaveformWidget — 采样波形，深色/亮色部分为已播放范围。'))
        layout.addWidget(BodyLabel('点击或拖动跳转；方向键移动 1 秒，Home / End 跳至首尾。'))
        self.fileLabel = BodyLabel('尚未选择文件', self)
        self.fileLabel.setWordWrap(True)
        layout.addWidget(self.fileLabel)
        self.waveform = AudioWaveformWidget(self)
        self.waveform.setFixedHeight(220)
        self.waveform.setSeekEnabled(False)
        layout.addWidget(self.waveform)
        self.status = BodyLabel(self)
        layout.addWidget(self.status)
        controls = QHBoxLayout()
        self.chooseButton = PushButton('选择音频文件', self)
        self.sampleButton = PushButton('加载测试 WAV', self)
        self.playButton = PushButton('播放', self)
        self.stopButton = PushButton('停止', self)
        theme = PushButton('切换主题', self)
        for button in (self.chooseButton, self.sampleButton, self.playButton, self.stopButton, theme):
            controls.addWidget(button)
        controls.addStretch()
        layout.addLayout(controls)
        hint = BodyLabel('此展示页显式使用可选解码类和播放器；波形 Widget 本身不依赖 QtMultimedia。', self)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()
        self.chooseButton.clicked.connect(self._chooseFile)
        self.sampleButton.clicked.connect(lambda: self.loadFile(SAMPLE_WAV))
        self.playButton.clicked.connect(self._togglePlay)
        self.stopButton.clicked.connect(self._stop)
        theme.clicked.connect(toggleTheme)
        self.decoder.samplesReady.connect(self.waveform.appendSamples)
        self.decoder.finished.connect(self._onDecoded)
        self.decoder.errorOccurred.connect(self._onDecodeError)
        self.player.positionChanged.connect(self.waveform.setPosition)
        self.player.playbackStateChanged.connect(self._onPlaybackState)
        self.player.mediaStatusChanged.connect(self._onMediaStatus)
        self.player.seekableChanged.connect(self._onSeekable)
        self.player.errorOccurred.connect(self._onPlaybackError)
        self.waveform.positionChanged.connect(self._updateStatus)
        self.waveform.durationChanged.connect(self._updateStatus)
        self.waveform.seekRequested.connect(self._onSeek)
        self._setReady(False)
        self._updateStatus()

    def _chooseFile(self):
        start = self._source.toLocalFile() or str(SAMPLE_WAV.parent)
        path, _ = QFileDialog.getOpenFileName(
            self, '选择音频文件', start,
            '音频文件 (*.wav *.mp3 *.flac *.ogg *.m4a *.aac);;所有文件 (*)')
        if path:
            self.loadFile(path)

    def loadFile(self, path):
        """Clear the previous stream before decoding a user-selected file."""
        self._loaded = False
        self.decoder.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        self._setReady(False)
        self.waveform.clear()
        self._source = QUrl.fromLocalFile(str(Path(path).resolve()))
        self.fileLabel.setText(self._source.toLocalFile())
        self._message = '正在解码音频…'
        self._updateStatus()
        self.decoder.decode(self._source)

    def _setReady(self, ready):
        self.playButton.setEnabled(ready)
        self.stopButton.setEnabled(ready)
        self.waveform.setSeekEnabled(ready and self.player.isSeekable())

    def _onDecoded(self):
        self._loaded = True
        self._message = '波形已加载，正在准备播放…'
        self._updateStatus()
        self.player.setSource(self._source)

    def _onDecodeError(self, message):
        self._loaded = False
        self.player.stop()
        self._setReady(False)
        self.waveform.clear()
        self._message = '解码失败：' + message
        self._updateStatus()

    def _onPlaybackError(self, error, message):
        if not self._loaded:
            return
        self._setReady(False)
        self._message = '播放失败：' + (message or str(error))
        self._updateStatus()

    def _onMediaStatus(self, status):
        if not self._loaded:
            return
        ready = status in (QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia,
                           QMediaPlayer.BufferingMedia, QMediaPlayer.EndOfMedia)
        self._setReady(ready)
        if status == QMediaPlayer.EndOfMedia:
            self.waveform.setPosition(self.waveform.duration())
            self._message = '播放完毕，可再次播放。'
        elif ready:
            self._message = '已就绪'
        self._updateStatus()

    def _onSeekable(self, seekable):
        self.waveform.setSeekEnabled(self._loaded and self.playButton.isEnabled() and seekable)

    def _onPlaybackState(self, state):
        self.playButton.setText('暂停' if state == QMediaPlayer.PlayingState else '播放')

    def _updateStatus(self, *args):
        self.status.setText(f'{self._message}  ·  {self.waveform.position() / 1000:.2f} / '
                            f'{self.waveform.duration() / 1000:.2f} 秒')

    def _stop(self):
        self.player.stop()
        self.waveform.setPosition(0)
        if self._loaded:
            self._message = '已停止'
            self._updateStatus()

    def _togglePlay(self):
        if not self._loaded or not self.playButton.isEnabled():
            return
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            return
        if self.player.mediaStatus() == QMediaPlayer.EndOfMedia or self.waveform.position() >= self.waveform.duration():
            self.player.setPosition(0)
            self.waveform.setPosition(0)
        self.player.play()

    def _onSeek(self, position):
        if self._loaded and self.player.isSeekable():
            self.player.setPosition(position)

    def hideEvent(self, event):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.decoder.stop()
        self.player.stop()
        super().closeEvent(event)
