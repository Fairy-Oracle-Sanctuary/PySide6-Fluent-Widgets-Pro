"""Dashboard card inheritance, custom contents, switch semantics and rendering."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget

from qfluentwidgets_pro import DashboardCardWidget, FluentIcon, SimpleCardWidget, Theme, setTheme


def run():
    app = QApplication([])
    owner = QWidget()
    owner.setObjectName('dashboardCardTestOwner')
    owner.setStyleSheet('QWidget#dashboardCardTestOwner { background: #808080; }')
    owner.resize(540, 480)
    card = DashboardCardWidget(FluentIcon.GLOBE, '<b>Caller title</b>', 'Caller description', owner)
    card.setGeometry(20, 20, 400, 160)
    assert isinstance(card, SimpleCardWidget)
    assert 'paintEvent' not in DashboardCardWidget.__dict__, 'Reuse SimpleCardWidget painting'
    assert card.borderRadius == 8 and card.content() == 'Caller description'
    assert card.titleLabel.textFormat() == card.contentLabel.textFormat() == Qt.PlainText
    assert card.switchButton.indicator.accessibleName() == card.title()
    assert not card.isChecked() and card.switchButton.onText == card.switchButton.offText == ''
    changes = []
    card.checkedChanged.connect(changes.append)
    owner.show()
    assert QTest.qWaitForWindowExposed(owner)
    owner.activateWindow()
    QTest.qWait(80)
    card.setChecked(True)
    card.setChecked(True)
    assert changes == [True]
    QTest.mouseClick(card.switchButton.indicator, Qt.LeftButton)
    assert not card.isChecked() and changes == [True, False]
    card.switchButton.indicator.setFocus()
    QTest.keyClick(card.switchButton.indicator, Qt.Key_Space)
    assert card.isChecked() and changes == [True, False, True]
    card.setEnabled(False)
    QTest.mouseClick(card.switchButton.indicator, Qt.LeftButton)
    assert changes == [True, False, True]
    card.setEnabled(True)
    card.setIcon(None)
    assert card.iconWidget.isHidden()
    card.setIcon(FluentIcon.SETTING)
    card.setIconSize(QSize(20, 20))
    assert not card.iconWidget.isHidden() and card.iconWidget.size() == QSize(20, 20)
    card.setSwitchVisible(False)
    assert card.switchButton.isHidden()
    card.setSwitchVisible(True)
    card.setTitle('New title')
    assert card.switchButton.accessibleName() == 'New title'
    card.setContent('')
    assert card.contentLabel.isHidden() and card.contentWidget.isHidden()
    custom = QPushButton('Open editor')
    clicks = []
    custom.clicked.connect(lambda: clicks.append(True))
    card.addWidget(custom)
    QTest.qWait(10)
    assert custom.parentWidget() is card.contentWidget and card.contentWidget.isVisible()
    QTest.mouseClick(custom, Qt.LeftButton)
    assert clicks == [True]
    card.setChecked(False)
    assert custom.isEnabled(), 'Business behavior must be application-owned'
    card.setContent('Description above custom controls')
    card.setContent('')
    assert card.contentLabel.isHidden() and not card.contentWidget.isHidden()
    row = QHBoxLayout()
    row.addWidget(QPushButton('Custom row'))
    card.addLayout(row)
    assert card.viewLayout.count() == 3
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        card.resetCardBackgroundColor()
        QTest.qWait(160)
        reference = SimpleCardWidget()
        assert card._normalBackgroundColor() == reference._normalBackgroundColor()
        reference.deleteLater()
        card.setCardBackgroundColor('#edf7fa', '#282e30')
        QTest.qWait(160)
        fill = '#282e30' if theme == Theme.DARK else '#edf7fa'
        image = card.grab().toImage()
        dpr = image.devicePixelRatio()
        assert image.pixelColor(round(8*dpr), round(70*dpr)).name() == fill
        assert card.backgroundColor.name() == fill
        # The inherited thin border differs from the fill, and corner is unfilled.
        assert image.pixelColor(round(200*dpr), round(dpr)).name() != fill
        ownerImage = owner.grab().toImage()
        assert ownerImage.pixelColor(round(card.x()*dpr), round(card.y()*dpr)).name() == '#808080'
        QTest.mouseMove(card, QPoint(5, 70))
        QTest.qWait(140)
        assert card.backgroundColor.name() == fill
    card.setCardBackgroundColor('#123456')
    setTheme(Theme.LIGHT)
    QTest.qWait(160)
    assert card.backgroundColor.name() == '#123456'
    setTheme(Theme.DARK)
    QTest.qWait(160)
    assert card.backgroundColor.name() == '#123456'
    old = card.backgroundColor
    for call, error in ((lambda: card.setCardBackgroundColor('invalid'), ValueError),
                        (lambda: card.setIconSize(QSize(0, 20)), ValueError),
                        (lambda: card.addWidget(card), ValueError),
                        (lambda: card.addWidget('invalid'), TypeError)):
        try:
            call()
        except error:
            pass
        else:
            raise AssertionError('Invalid card setting accepted')
    assert card.backgroundColor == old
    card.resize(220, 240)
    card.setTitle('Long title that wraps without obscuring the switch')
    card.setContent('A long description that wraps naturally in a narrow dashboard card.')
    QTest.qWait(30)
    assert card.titleLabel.geometry().right() < card.switchButton.geometry().left()
    assert card.contentLabel.width() <= card.contentWidget.width()
    from gallery.view.dashboard_card_demo import DashboardCardDemo
    demo = DashboardCardDemo()
    demo.resize(900, 650)
    demo.show()
    QTest.qWait(100)
    assert isinstance(demo.featureCard, SimpleCardWidget) and demo.featureCard.isChecked()
    demo.customCard.setChecked(True)
    assert '开启' in demo.status.text()
    demo.openButton.click()
    assert '已点击' in demo.status.text()
    assert 75 <= demo.featureCard.height() <= 90
    assert 90 <= demo.customCard.height() <= 110
    demo.close()
    owner.close()
    print('PASS: SimpleCardWidget inheritance/painting, switch signals/mouse/keyboard, caller text, '
          'custom widgets/layouts, accessibility, theme fills/reset/border, narrow layout and demo')


if __name__ == '__main__':
    run()
