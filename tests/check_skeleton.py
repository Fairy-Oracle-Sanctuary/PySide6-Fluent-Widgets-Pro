"""Native geometry, shimmer, lifecycle and theme regression tests."""

import sys
from math import atan2, degrees
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QAbstractAnimation, QPointF, QRectF
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from qfluentwidgets_pro import (
    ArticleSkeleton, CirclePersonalInfoSkeleton, RectanglePersonalInfoSkeleton,
    SkeletonWidget, Theme, setTheme,
)


def pixel(image, x, y):
    scale = image.devicePixelRatio()
    return image.pixelColor(round(x * scale), round(y * scale))


def run():
    app = QApplication([])
    owner = QWidget()
    owner.setStyleSheet('background: #15314b;')
    owner.resize(560, 160)
    skeleton = SkeletonWidget(owner)
    skeleton.resize(520, 100)
    skeleton.move(10, 10)
    source = QRectF(0, 0, 100, 100)
    skeleton.addEllipse(source)
    source.setWidth(10)  # Geometry must be copied rather than alias caller state.
    skeleton.addRect(QRectF(120, 10, 400, 30))
    skeleton.addRect(QRectF(120, 60, 200, 30))
    assert skeleton.skeletonPath().contains(QPointF(50, 50))
    assert not skeleton.skeletonPath().contains(QPointF(1, 1))
    owner.show()
    QTest.qWait(30)
    assert skeleton._animation.state() == QAbstractAnimation.Running
    assert skeleton.accessibleName() == 'Loading'
    assert skeleton.animationDuration() == 1500
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        skeleton.setAnimationEnabled(True)
        skeleton._animation.pause()
        skeleton._setPhase(0)
        start = skeleton.grab().toImage()
        assert pixel(start, 50, 50) == skeleton.baseColor()
        assert pixel(start, 110, 50).name() == '#15314b'
        skeleton._setPhase(.5)
        gradient = skeleton._shimmerGradient()
        direction = gradient.finalStop() - gradient.start()
        assert abs(degrees(atan2(direction.y(), direction.x())) - 30) < 1e-10
        middle = skeleton.grab().toImage()
        assert pixel(middle, 260, 20).lightness() >= pixel(start, 260, 20).lightness() + 15
        assert pixel(middle, 110, 50) == pixel(start, 110, 50)
        assert pixel(middle, 500, 80) == pixel(start, 500, 80)
        skeleton._setPhase(1)
        assert skeleton.grab().toImage() == start  # No discontinuity when looping.
        skeleton.setAnimationEnabled(False)
        assert skeleton.grab().toImage() == start
        assert skeleton._animation.state() == QAbstractAnimation.Stopped

    skeleton.setAnimationDuration(600)
    skeleton.setAnimationEnabled(True)
    QTest.qWait(90)
    assert skeleton._phase > 0
    phase = skeleton._phase
    owner.hide()
    assert skeleton._animation.state() == QAbstractAnimation.Paused
    QTest.qWait(60)
    assert skeleton._phase == phase
    owner.show()
    QTest.qWait(60)
    assert skeleton._animation.state() == QAbstractAnimation.Running and skeleton._phase > phase
    skeleton.hide()
    skeleton.setAnimationEnabled(False)
    skeleton.show()
    QTest.qWait(20)
    assert skeleton._animation.state() == QAbstractAnimation.Stopped
    skeleton.setColors('#aaaabb', '#445566', QColor(255, 0, 0, 30), QColor(0, 255, 0, 30))
    assert skeleton.baseColor().name() == '#445566'
    color = skeleton.baseColor()
    color.setRed(255)
    assert skeleton.baseColor().name() == '#445566'
    skeleton.clear()
    assert skeleton.skeletonPath().isEmpty()
    skeleton.addRect(QRectF(.25, .1, .5, .3), relative=True)
    for width in (200, 520):
        skeleton.resize(width, 100)
        path = skeleton.skeletonPath()
        assert path.boundingRect() == QRectF(width * .25, 10, width * .5, 30)
    for invalid in (QRectF(0, 0, -1, 20), QRectF(0, 0, 0, 10), QRectF(float('nan'), 0, 10, 10)):
        try:
            skeleton.addRect(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid skeleton geometry accepted')
    for call in (lambda: skeleton.setAnimationDuration(0),
                 lambda: skeleton.addRect(QRectF(0, 0, 10, 10), float('inf')),
                 lambda: skeleton.setColors('invalid', 'white')):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid skeleton option accepted')
    # Overlapping custom shapes must not cut holes in one another.
    skeleton.clear()
    skeleton.addRect(QRectF(0, 0, 40, 40), 0)
    skeleton.addRect(QRectF(20, 20, 40, 40), 0)
    assert skeleton.skeletonPath().contains(QPointF(30, 30))
    # The rendered band's peak leans right at the top (clockwise from vertical).
    skeleton.clear()
    skeleton.resize(520, 200)
    skeleton.addRect(QRectF(0, 0, 520, 200), 0)
    skeleton.setColors('#e5e5e5', '#3d3d3d', QColor(255, 255, 255, 220), QColor(255, 255, 255, 80))
    skeleton.setAnimationEnabled(True)
    skeleton._animation.pause()
    skeleton._setPhase(.5)
    diagonal = skeleton.grab().toImage()
    def peak(y):
        row = [pixel(diagonal, x, y).lightness() for x in range(520)]
        positions = [x for x, value in enumerate(row) if value == max(row)]
        return sum(positions) / len(positions)
    assert 78 < peak(30) - peak(170) < 84
    for cls in (ArticleSkeleton, CirclePersonalInfoSkeleton, RectanglePersonalInfoSkeleton):
        preset = cls()
        for width in (0, 80, 320, preset.sizeHint().width(), 800):
            preset.resize(width, preset.sizeHint().height())
            bounds = preset.skeletonPath().boundingRect()
            assert bounds.left() >= 0 and bounds.top() >= 0
            assert bounds.right() <= width and bounds.bottom() <= preset.height()
        preset.resize(preset.sizeHint())
        path = preset.skeletonPath()
        assert path.contains(QPointF(50, 50))
        assert not path.contains(QPointF(120, 50))
        assert path.contains(QPointF(150, 20))
        if cls is CirclePersonalInfoSkeleton:
            assert not path.contains(QPointF(5, 5))
        else:
            assert path.contains(QPointF(5, 5))
        preset.close()
    from gallery_fixtures.skeleton_demo import SkeletonDemo
    demo = SkeletonDemo()
    demo.resize(900, 850)
    demo.show()
    QTest.qWait(30)
    demo.animationCheckBox.setChecked(False)
    assert all(not w.isAnimationEnabled() for w in demo.skeletons)
    demo.animationCheckBox.setChecked(True)
    assert all(w.isAnimationEnabled() for w in demo.skeletons)
    custom = demo.skeletons[-1]
    for width in (320, 520, 1100):
        custom.resize(width, 100)
        path = custom.skeletonPath()
        avatar = min(100., width / 4)
        assert not path.contains(QPointF(avatar + 10, 20))
        assert not path.contains(QPointF(avatar + 19, 20))
        assert path.contains(QPointF(avatar + 21, 20))
        assert path.contains(QPointF(avatar + 21, 70))
        assert path.boundingRect().right() <= width
    demo.close()
    owner.close()
    print('PASS: skeleton presets/custom geometry, clipping, shimmer frames, looping, hidden pause/resume, '
          'static mode, colors, narrow layouts, validation and demo controls')


if __name__ == '__main__':
    run()
