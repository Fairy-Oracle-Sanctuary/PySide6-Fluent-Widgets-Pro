"""Deterministic Qt tests: synthetic screens only; never capture the user's desktop."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QCursor, QFontMetrics, QImage, QPainter, QPixmap
from PySide6.QtTest import QTest
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import FluentIcon, PushButton, ScreenColorPicker, Theme, setTheme, themeColor
import qfluentwidgets_pro.components.widgets.screen_color_picker as pickerModule
from qfluentwidgets_pro.components.widgets.screen_color_picker import (
    _ColorPreview, _PickerOverlay, _captureLiveColor, _previewPosition, _sampleImage,
)
from gallery_fixtures.color_picker_demo import ColorPickerDemo


def image(width, height, color):
    result = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    result.fill(QColor(color))
    return result


def render(widget, scale=1):
    QApplication.processEvents()
    result = image(widget.width() * scale, widget.height() * scale, 'transparent')
    result.setDevicePixelRatio(scale)
    widget.render(result, QPoint(), renderFlags=QWidget.DrawChildren)
    return result


class FakeScreen:
    def __init__(self, geometry, screenshot):
        self.rect, self.image, self.calls = geometry, screenshot, []
        self.regions = []

    def geometry(self):
        return QRect(self.rect)

    def grabWindow(self, window, *region):
        self.calls.append(window)
        self.regions.append(region)
        return QPixmap.fromImage(self.image)


def run():
    app = QApplication([])
    setTheme(Theme.LIGHT)
    accent = QColor(themeColor())
    owner = QWidget()
    owner.resize(300, 220)
    picker = ScreenColorPicker('#0078D4', owner)
    picker.resize(picker.sizeHint())
    picker.move(90, 140)
    owner.show()
    QTest.qWait(10)
    assert picker.sizeHint() == QSize(60, 32) and isinstance(picker, PushButton)
    assert picker.isFreezeScreenEnabled()
    assert picker.color() == QColor('#0078D4') and not picker.isPicking()
    changed, picked, hovered, states, canceled, errors = [], [], [], [], [], []
    picker.colorChanged.connect(lambda color: changed.append(QColor(color)))
    picker.colorPicked.connect(lambda color: picked.append(QColor(color)))
    picker.colorHovered.connect(lambda color: hovered.append(QColor(color)))
    picker.pickingChanged.connect(states.append)
    picker.pickingCanceled.connect(lambda: canceled.append(True))
    picker.errorOccurred.connect(errors.append)
    copy = picker.color()
    copy.setRed(255)
    assert picker.color() == QColor('#0078D4')
    picker.setColor('red')
    picker.setColor('red')
    assert changed == [QColor('red')] and not picked
    for invalid in (QColor(), 'not-a-color', object()):
        try:
            picker.setColor(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid color accepted')
    assert picker.color() == QColor('red')

    # Capture uses screen-local grabWindow(0); no capture happens on import/construction.
    first = FakeScreen(QRect(0, 0, 300, 240), image(600, 480, '#102030'))
    first.image.setDevicePixelRatio(2)
    second = FakeScreen(QRect(-300, -240, 300, 240), image(375, 300, '#246824'))
    second.image.setDevicePixelRatio(1.25)
    with patch.object(QApplication, 'screens', return_value=[first, second]):
        snapshots = picker._captureScreens()
    assert first.calls == second.calls == [0]
    assert snapshots[0][2].size() == QSize(600, 480)
    # Physical sampling including negative origins, fractional DPI and fractional positions.
    for geometry, screenshot in ((first.rect, first.image), (second.rect, second.image)):
        for point in (QPointF(geometry.x(), geometry.y()),
                      QPointF(geometry.x() + 19.6, geometry.y() + 13.2),
                      QPointF(geometry.x() + geometry.width() - .1, geometry.y() + geometry.height() - .1)):
            x = int((point.x() - geometry.x()) * screenshot.width() / geometry.width())
            y = int((point.y() - geometry.y()) * screenshot.height() / geometry.height())
            screenshot.setPixelColor(x, y, QColor('#FF1493'))
            assert _sampleImage(screenshot, geometry, point) == QColor('#FF1493')
        assert not _sampleImage(screenshot, geometry, QPoint(geometry.x() + geometry.width(), geometry.y())).isValid()
        assert not _sampleImage(screenshot, geometry, QPoint(geometry.x() - 1, geometry.y())).isValid()
    assert not _sampleImage(QImage(), first.rect, QPoint()).isValid()
    assert not _sampleImage(first.image, QRect(), QPoint()).isValid()
    tiny = image(2, 2, 'red')
    tiny.setPixelColor(1, 1, QColor('yellow'))
    liveScreen = FakeScreen(second.rect, tiny)
    assert _captureLiveColor(liveScreen, second.rect, QPointF(-289.4, -226.2)) == QColor('yellow')
    assert liveScreen.regions == [(10, 13, 1, 1)]
    brokenPixel = FakeScreen(second.rect, QImage())
    try:
        _captureLiveColor(brokenPixel, second.rect, QPoint(-250, -200))
    except RuntimeError:
        pass
    else:
        raise AssertionError('Null live capture accepted')
    # Preview stays inside the active monitor, not the desktop's bounding box.
    preview = _ColorPreview(owner)
    assert preview.card.size() == QSize(106, 40)
    assert preview.size() == QSize(138, 76)
    assert preview.card.font().pixelSize() == 14
    # Windows offscreen uses a fallback font (missing native system glyphs).
    if QApplication.platformName() == 'windows':
        assert QFontMetrics(preview.card.font()).horizontalAdvance('#ffffff') <= 58
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        preview.setColor(QColor('#123456'))
        for scale in (1, 2):
            # Render without shadow to measure the card itself rather than its halo.
            preview.card.graphicsEffect().setEnabled(False)
            raster = render(preview.card, scale)
            assert raster.size() == QSize(106 * scale, 40 * scale)
            assert raster.pixelColor(20 * scale, 20 * scale) == QColor('#123456')
            background = QColor('#2B2B2B' if theme == Theme.DARK else '#F7F7F7')
            assert raster.pixelColor(38 * scale, 20 * scale) == background
            assert raster.pixelColor(20 * scale, 37 * scale) == background
    preview.deleteLater()
    setTheme(Theme.LIGHT)
    bounds, size = QRect(0, 0, 300, 240), QSize(138, 76)
    for point in (QPoint(0, 0), QPoint(299, 239), QPoint(299, 0), QPoint(0, 239), QPoint(150, 120)):
        position = _previewPosition(point, bounds, size)
        assert bounds.contains(QRect(position, size))

    primary = QApplication.primaryScreen()
    capture = image(600, 480, '#102030')
    painter = QPainter(capture)
    painter.fillRect(0, 0, 120, 480, QColor('#ABCDEF'))
    painter.end()
    capture.setDevicePixelRatio(2)
    negative = image(375, 300, '#246824')
    negative.setDevicePixelRatio(1.25)
    # Real Qt windows/events, injected desktop snapshots. No OS screen capture.
    fixtures = [(primary, first.rect, capture), (primary, second.rect, negative)]
    with patch.object(picker, '_captureScreens', return_value=fixtures), patch.object(QCursor, 'pos', return_value=QPoint(90, 90)):
        QTest.mouseClick(picker, Qt.LeftButton, pos=QPoint(54, 20))
        assert picker.isPicking() and picker._timer.isActive() and states == [True]
        assert len(picker._overlays) == 2
        overlay, other = picker._overlays
        assert overlay.screenGeometry == first.rect and other.screenGeometry == second.rect
        # Drawing a high-DPI screenshot also samples the same physical region.
        for scale in (1, 2):
            raster = render(overlay, scale)
            assert raster.pixelColor(20 * scale, 30 * scale) == QColor('#ABCDEF')
            assert raster.pixelColor(80 * scale, 30 * scale) == QColor('#102030')
        hovered.clear()
        picker._previewAt(QPoint(20, 30))
        picker._previewAt(QPoint(20, 30))
        assert hovered == [QColor('#ABCDEF')] and picker.color() == QColor('red')
        assert overlay.preview.isVisible() and not other.preview.isVisible()
        picker._previewAt(QPoint(-299, -239))
        assert hovered[-1] == QColor('#246824')
        assert other.preview.isVisible() and not overlay.preview.isVisible()
        picker._previewAt(QPoint(400, 400))  # gap / outside all screens
        assert not overlay.preview.isVisible() and not other.preview.isVisible()
        picker._confirmAt(QPoint(400, 400))
        assert picker.isPicking()
        picker._previewAt(QPoint(20, 30))
        point = overlay.preview.pos() + QPoint(20, 20)
        expected = _sampleImage(capture, first.rect, point)
        assert overlay.colorAt(point) == expected  # card never contaminates sampling
        QTest.mouseClick(overlay, Qt.LeftButton, pos=QPoint(90, 90))
        assert picker.color() == QColor('#102030') and picked == [QColor('#102030')]
        assert states == [True, False] and not picker.isPicking() and not picker._timer.isActive()
        assert not picker._overlays and overlay._image.isNull() and other._image.isNull()
        assert not canceled and themeColor() == accent
        changes = len(changed)
        assert picker.startPicking()
        assert not picker.startPicking()  # reentry does not capture twice
        QTest.keyClick(picker._overlays[0], Qt.Key_Return)
        assert len(picked) == 2 and len(changed) == changes  # same color explicitly picked again
        assert not picker.isPicking()
        assert picker.startPicking()
        picker._previewAt(QPoint(20, 30))
        QTest.keyClick(picker._overlays[0], Qt.Key_Escape)
        assert len(canceled) == 1 and picker.color() == QColor('#102030')
        assert picker.startPicking()
        QTest.mouseClick(picker._overlays[0], Qt.RightButton, pos=QPoint(20, 30))
        assert len(canceled) == 2 and len(picked) == 2
        rival = ScreenColorPicker(owner)
        with patch.object(rival, '_captureScreens', return_value=fixtures) as rivalCapture:
            assert picker.startPicking()
            assert not rival.startPicking()
            assert rivalCapture.call_count == 0
            picker.cancelPicking()
            assert rival.startPicking()
            rival.cancelPicking()
        assert picker.startPicking()
        picker.setEnabled(False)
        assert not picker.isPicking() and not picker.startPicking()
        picker.setEnabled(True)
        assert picker.startPicking()
        picker.hide()
        assert not picker.isPicking()
        picker.show()
        assert picker.startPicking()
        QApplication.sendEvent(app, QEvent(QEvent.ApplicationDeactivate))
        assert not picker.isPicking()
        assert picker.startPicking()
        primary.geometryChanged.emit(primary.geometry())
        assert not picker.isPicking()
        assert picker.startPicking()
        app.screenRemoved.emit(primary)
        assert not picker.isPicking()
        assert picker.startPicking()
        app.screenAdded.emit(primary)
        assert not picker.isPicking()
        assert picker.startPicking()
        primary.logicalDotsPerInchChanged.emit(primary.logicalDotsPerInch())
        assert not picker.isPicking()
        assert picker.startPicking()
        picker._overlays[0].close()
        assert not picker.isPicking()
        assert picker.startPicking()
        picker.cancelPicking()
        cancellations = len(canceled)
        picker.cancelPicking()
        assert len(canceled) == cancellations
        with patch.object(QCursor, 'pos', return_value=QPoint(-250, -200)):
            assert picker.startPicking()
            QTest.keyClick(picker._overlays[1], Qt.Key_Space)
            assert picker.color() == QColor('#246824') and not picker.isPicking()
        # Cancel from a preview callback must not restart the cursor timer.
        picker.colorHovered.connect(picker.cancelPicking)
        assert picker.startPicking()
        assert not picker.isPicking() and not picker._timer.isActive()
        picker.colorHovered.disconnect(picker.cancelPicking)

    baseline, transitions = picker.color(), len(states)
    for badSnapshots in ([], [(primary, first.rect, QImage())], [(primary, QRect(), capture)]):
        with patch.object(picker, '_captureScreens', return_value=badSnapshots):
            assert not picker.startPicking()
        assert picker.color() == baseline and len(states) == transitions and not picker.isPicking()
    with patch.object(picker, '_captureScreens', side_effect=RuntimeError('permission denied')):
        assert not picker.startPicking() and errors[-1] == 'permission denied'
    broken = FakeScreen(first.rect, QImage())
    with patch.object(QApplication, 'screens', return_value=[broken]):
        assert not picker.startPicking()
    with patch.object(QApplication, 'screens', return_value=[]):
        assert not picker.startPicking()
    assert not picker._overlays and not picker._timer.isActive()

    # Partial construction failure disposes the first overlay and its screenshot.
    constructed, originalInit = [], _PickerOverlay.__init__
    def failSecond(overlay, *args):
        if constructed:
            raise RuntimeError('overlay initialization failed')
        originalInit(overlay, *args)
        constructed.append(overlay)
    with patch.object(picker, '_captureScreens', return_value=fixtures), patch.object(_PickerOverlay, '__init__', failSecond):
        assert not picker.startPicking()
    assert errors[-1] == 'overlay initialization failed'
    assert constructed[0]._image.isNull() and not constructed[0].isVisible()
    assert not picker._overlays and not picker._timer.isActive()

    # Live mode uses transparent, capture-excluded overlays and refreshes even
    # with a stationary pointer. Sampling is mocked; the desktop is never read.
    picker.setFreezeScreenEnabled(False)
    assert not picker.isFreezeScreenEnabled()
    QApplication.processEvents()  # Finish deferred destruction/activation from previous sessions.
    liveColor = [QColor('#112233')]
    def currentPixel(screen, geometry, position):
        return QColor(liveColor[0])
    with patch.object(picker, '_captureScreens', return_value=fixtures), \
            patch.object(pickerModule, '_excludeFromCapture') as exclude, \
            patch.object(pickerModule, '_captureLiveColor', side_effect=currentPixel) as sample, \
            patch.object(QCursor, 'pos', return_value=QPoint(90, 90)):
        assert picker.startPicking()
        picker._timer.stop()  # Deterministic manual timer ticks.
        assert exclude.call_count == 2
        assert all(o.testAttribute(Qt.WA_TranslucentBackground) and o._image.isNull() for o in picker._overlays)
        liveOverlay = picker._overlays[0]
        assert render(liveOverlay).pixelColor(20, 30).alpha() <= 1
        committed, confirmations = picker.color(), len(picked)
        liveColor[0] = QColor('#445566')
        picker._updateFromCursor()
        assert picker._hoverColor == liveColor[0] and picker.color() == committed
        liveColor[0] = QColor('#778899')
        picker._previewAt(QPoint(90, 90))
        assert picker._hoverColor == liveColor[0]  # same coordinate, fresh pixel
        liveColor[0] = QColor('#ABC123')
        QTest.mouseClick(liveOverlay, Qt.LeftButton, pos=QPoint(90, 90))
        assert picker.color() == liveColor[0] and len(picked) == confirmations + 1
        assert sample.call_count >= 4 and not picker.isPicking()
        assert picker.startPicking()
        picker.setFreezeScreenEnabled(False)  # no-op does not cancel
        assert picker.isPicking()
        committed = picker.color()
        picker.setFreezeScreenEnabled(True)
        assert not picker.isPicking() and not picker._timer.isActive() and picker.color() == committed
        assert picker.startPicking()
        assert not picker._overlays[0].testAttribute(Qt.WA_TranslucentBackground)
        picker.cancelPicking()
        picker.setFreezeScreenEnabled(False)
        assert picker.startPicking()
        with patch.object(pickerModule, '_captureLiveColor', side_effect=RuntimeError('live capture lost')):
            picker._previewAt(QPoint(90, 90))
        assert not picker.isPicking() and errors[-1] == 'live capture lost'
        assert picker.color() == committed and not picker._overlays and not picker._timer.isActive()
    with patch.object(picker, '_captureScreens', return_value=fixtures), \
            patch.object(pickerModule, '_excludeFromCapture', side_effect=RuntimeError('live unsupported')):
        assert not picker.startPicking()
        assert errors[-1] == 'live unsupported' and not picker._overlays and not picker._timer.isActive()
    picker.setFreezeScreenEnabled(True)

    # Button visuals: chosen swatch is independent of theme accent, also at 2x.
    picker.setColor('#C42B1C')
    picker.clearFocus()
    picker.setAttribute(Qt.WA_UnderMouse, False)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        for scale in (1, 2):
            raster = render(picker, scale)
            assert raster.pixelColor(20 * scale, 20 * scale) == QColor('#C42B1C')
            assert raster.pixelColor(0, 0).alpha() == 0
    setTheme(Theme.LIGHT)
    picker.setEnabled(False)
    assert 0 < render(picker).pixelColor(20, 20).alpha() < 255
    picker.setEnabled(True)
    assert themeColor() == accent
    # Standard button QSS owns all background/border states, not hand-picked colors.
    reference = PushButton(owner)
    reference.resize(picker.size())
    reference.move(180, 140)
    reference.show()
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        colorName = 'black' if theme == Theme.LIGHT else 'white'
        assert FluentIcon.EYEDROPPER.path().endswith('Eyedropper_%s.svg' % colorName)
        embeddedIcon = QSvgRenderer(FluentIcon.EYEDROPPER.path())
        sourceIcon = QSvgRenderer(str(Path(__file__).resolve().parents[1] /
                                     'qfluentwidgets_pro/_rc/images/icons' /
                                     ('Eyedropper_%s.svg' % colorName)))
        assert embeddedIcon.isValid() and sourceIcon.isValid()
        for enabled, hover, down in ((True, False, False), (True, True, False),
                                     (True, True, True), (False, False, False)):
            for button in (picker, reference):
                button.setEnabled(enabled)
                button.setDown(down)
                button.setAttribute(Qt.WA_UnderMouse, hover)
                QApplication.sendEvent(button, QEvent(QEvent.Enter if hover else QEvent.Leave))
            actual, expected = render(picker), render(reference)
            assert picker.styleSheet().strip() == reference.styleSheet().strip()
            for point in ((30, 16), (30, 0), (30, 31), (1, 16)):
                assert actual.pixelColor(*point) == expected.pixelColor(*point), (theme, enabled, hover, down, point)
            # The embedded glyph must exactly match the supplied SVG at both DPIs,
            # retaining button foreground opacity in pressed and disabled states.
            for scale in (1, 2):
                actual, expected = render(picker, scale), render(reference, scale)
                painter = QPainter(expected)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setOpacity(.3628 if not enabled else (.786 if down else 1))
                sourceIcon.render(painter, QRectF(36, 8, 16, 16))
                painter.end()
                rect = QRect(36 * scale, 8 * scale, 16 * scale, 16 * scale)
                assert actual.copy(rect) == expected.copy(rect), (theme, enabled, hover, down, scale)
    picker.setEnabled(True)
    picker.setDown(False)
    reference.hide()
    setTheme(Theme.LIGHT)
    demo = ColorPickerDemo()
    assert isinstance(demo.screenPicker, ScreenColorPicker)
    assert demo.freezeScreenCheckBox.isChecked()
    demo.freezeScreenCheckBox.setChecked(False)
    assert not demo.screenPicker.isFreezeScreenEnabled()
    demo.freezeScreenCheckBox.setChecked(True)
    assert demo.screenPicker.isFreezeScreenEnabled()
    demo.screenPicker.setColor('#ABCDEF')
    assert '#abcdef' in demo.screenColorLabel.text()
    with patch.object(demo.screenPicker, '_captureScreens', side_effect=RuntimeError('capture denied')):
        assert not demo.screenPicker.startPicking()
        assert demo.screenMessageLabel.text() == 'capture denied'

    # Native Qt preview with an artificial white background, not a desktop screenshot.
    picker.setColor('#0078D4')
    preview = _ColorPreview(owner)
    preview.move(48, 20)
    preview.show()
    picker.clearFocus()
    picker.setAttribute(Qt.WA_UnderMouse, False)
    QApplication.processEvents()
    raster = image(300, 220, 'white')
    painter = QPainter(raster)
    painter.drawImage(0, 0, render(owner))
    painter.end()
    path = str(Path(tempfile.gettempdir()) / 'codex-screen-color-picker-preview.png')
    assert raster.save(path)
    demo.close()
    owner.close()
    print('PASS: Qt overlay events, preview/confirm/cancel, cleanup, failure handling, frozen sampling, '
          'negative-origin mixed-DPI/fractional mapping, 1x/2x drawing, independent colors and gallery')
    print('Preview:', path)


if __name__ == '__main__':
    run()
