"""Exercise the file chooser, bundled WAV, real muted playback and recovery."""
import os
import sys
import tempfile
import wave
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
if sys.platform == 'win32':
    os.environ.setdefault('QT_MEDIA_BACKEND', 'windows')

from PySide6.QtCore import QElapsedTimer, QPoint, Qt
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from gallery.view.audio_waveform_demo import AudioWaveformDemo, SAMPLE_WAV


def wait_until(predicate):
    timer = QElapsedTimer()
    timer.start()
    while not predicate() and timer.elapsed() < 10000:
        QTest.qWait(20)
    assert predicate(), 'Audio gallery timed out'


def run():
    app = QApplication([])
    with wave.open(str(SAMPLE_WAV), 'rb') as sample:
        assert sample.getparams()[:4] == (1, 2, 24000, 120000)
    demo = AudioWaveformDemo()
    demo.audioOutput.setMuted(True)  # never unexpectedly play sound during tests
    demo.resize(750, 450)
    demo.show()
    app.processEvents()
    assert not demo.playButton.isEnabled() and demo.waveform.duration() == 0
    with patch('gallery.view.audio_waveform_demo.QFileDialog.getOpenFileName',
               return_value=(str(SAMPLE_WAV), '音频文件')) as dialog:
        demo.chooseButton.click()
        dialog.assert_called_once()
    wait_until(lambda: demo.playButton.isEnabled())
    assert demo._loaded and not demo.decoder.isDecoding()
    assert demo.waveform.sampleCount() == 120000 and demo.waveform.duration() == 5000
    assert demo.player.source().toLocalFile() == str(SAMPLE_WAV).replace('\\', '/')
    assert demo.player.duration() == 5000 and demo.waveform.isSeekEnabled()
    # Cancelling the chooser preserves the already-loaded recording/source.
    with patch('gallery.view.audio_waveform_demo.QFileDialog.getOpenFileName',
               return_value=('', '')):
        demo.chooseButton.click()
    assert demo.waveform.sampleCount() == 120000 and demo._loaded
    demo.playButton.click()
    wait_until(lambda: demo.player.playbackState() == QMediaPlayer.PlayingState)
    wait_until(lambda: demo.waveform.position() >= 100)
    assert demo.playButton.text() == '暂停'
    demo.playButton.click()
    wait_until(lambda: demo.player.playbackState() == QMediaPlayer.PausedState)
    QTest.mouseClick(demo.waveform, Qt.LeftButton,
                     pos=QPoint(demo.waveform.width() // 2, 110))
    wait_until(lambda: abs(demo.player.position() - 2500) < 30)
    assert abs(demo.waveform.position() - demo.player.position()) < 30
    demo.stopButton.click()
    wait_until(lambda: demo.player.playbackState() == QMediaPlayer.StoppedState)
    assert demo.waveform.position() == 0
    # Navigation away pauses audio instead of leaving it playing in the background.
    demo.playButton.click()
    wait_until(lambda: demo.player.playbackState() == QMediaPlayer.PlayingState)
    demo.hide()
    wait_until(lambda: demo.player.playbackState() == QMediaPlayer.PausedState)
    demo.show()
    demo.stopButton.click()
    with tempfile.TemporaryDirectory(prefix='codex-waveform-gallery-') as temp:
        bad = Path(temp) / 'invalid.wav'
        bad.write_bytes(b'not a wave file')
        demo.loadFile(bad)
        wait_until(lambda: '解码失败' in demo.status.text())
        assert not demo.playButton.isEnabled() and not demo._loaded
        assert demo.waveform.sampleCount() == 0
        demo.sampleButton.click()
        wait_until(lambda: demo.playButton.isEnabled())
        assert demo.waveform.sampleCount() == 120000
        # Switching files immediately must not append data from an older decode.
        demo.loadFile(SAMPLE_WAV)
        demo.loadFile(SAMPLE_WAV)
        wait_until(lambda: demo.playButton.isEnabled())
        assert demo.waveform.sampleCount() == 120000
    demo.close()
    assert not demo.decoder.isDecoding() and demo.player.playbackState() == QMediaPlayer.StoppedState
    print('PASS: bundled 5-second WAV, file chooser/cancel, real muted playback, pause/stop/seek, hide pause, failure recovery and rapid file switching')


if __name__ == '__main__':
    run()
