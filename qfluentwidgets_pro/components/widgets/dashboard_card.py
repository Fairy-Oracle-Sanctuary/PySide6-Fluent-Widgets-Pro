"""Compact dashboard feature cards built on SimpleCardWidget."""

from PySide6.QtCore import Property, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import QHBoxLayout, QLayout, QSizePolicy, QVBoxLayout, QWidget

from ...common.style_sheet import isDarkTheme
from .card_widget import SimpleCardWidget
from .icon_widget import IconWidget
from .label import BodyLabel, CaptionLabel
from .switch_button import SwitchButton


class DashboardCardWidget(SimpleCardWidget):
    """Icon/title/switch header with descriptive text and arbitrary native content.

    Inherits SimpleCardWidget's painting, border and background animation. The
    switch only reports state; enabling a feature or handling a custom button
    remains the application's responsibility. Caller text is never translated.
    """

    checkedChanged = Signal(bool)

    def __init__(self, icon=None, title='', content='', parent=None):
        # BackgroundColorObject calls _normalBackgroundColor during super init.
        self._lightBackground = QColor()
        self._darkBackground = QColor()
        super().__init__(parent)
        self.setBorderRadius(8)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(16, 16, 16, 16)
        self.vBoxLayout.setSpacing(12)
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(12)
        self.iconWidget = IconWidget(self)
        self.iconWidget.setFixedSize(24, 24)
        self.titleLabel = BodyLabel(self)
        self.titleLabel.setTextFormat(Qt.PlainText)
        self.titleLabel.setWordWrap(True)
        font = self.titleLabel.font()
        font.setWeight(QFont.DemiBold)
        self.titleLabel.setFont(font)
        self.switchButton = SwitchButton(self)
        self.switchButton.setOnText('')
        self.switchButton.setOffText('')
        self.switchButton.setSpacing(0)
        self.switchButton.label.hide()
        self.switchButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.headerLayout.addWidget(self.iconWidget, 0, Qt.AlignTop)
        self.headerLayout.addWidget(self.titleLabel, 1)
        self.headerLayout.addWidget(self.switchButton, 0, Qt.AlignTop)
        self.vBoxLayout.addLayout(self.headerLayout)
        self.contentWidget = QWidget(self)
        self.viewLayout = QVBoxLayout(self.contentWidget)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(8)
        self.contentLabel = CaptionLabel(self.contentWidget)
        self.contentLabel.setTextFormat(Qt.PlainText)
        self.contentLabel.setWordWrap(True)
        self.contentLabel.setTextColor(QColor('#606060'), QColor('#cecece'))
        self.viewLayout.addWidget(self.contentLabel)
        self.vBoxLayout.addWidget(self.contentWidget)
        self.switchButton.checkedChanged.connect(self.checkedChanged)
        self.setIcon(icon)
        self.setTitle(title)
        self.setContent(content)

    def icon(self):
        return self.iconWidget.icon

    def setIcon(self, icon):
        self.iconWidget.setIcon(QIcon() if icon is None else icon)
        self.iconWidget.setVisible(icon is not None)

    def setIconSize(self, size):
        size = QSize(size)
        if size.width() <= 0 or size.height() <= 0:
            raise ValueError('Icon size must be positive')
        self.iconWidget.setFixedSize(size)

    def title(self):
        return self.titleLabel.text()

    def setTitle(self, title):
        title = str(title)
        self.titleLabel.setText(title)
        self.titleLabel.setVisible(bool(title))
        self.switchButton.setAccessibleName(title)
        self.switchButton.indicator.setAccessibleName(title)

    def content(self):
        return self.contentLabel.text()

    def setContent(self, content):
        content = str(content)
        self.contentLabel.setText(content)
        self.contentLabel.setVisible(bool(content))
        self.contentWidget.setVisible(bool(content) or self.viewLayout.count() > 1)

    def addWidget(self, widget, stretch=0, alignment=Qt.Alignment()):
        """Append application-owned content under the header/description."""
        if not isinstance(widget, QWidget):
            raise TypeError('Dashboard card content must be a QWidget')
        if widget is self or widget.isAncestorOf(self.contentWidget):
            raise ValueError('Dashboard card cannot contain itself or ancestors')
        self.viewLayout.addWidget(widget, stretch, alignment)
        self.contentWidget.show()

    def addLayout(self, layout, stretch=0):
        if not isinstance(layout, QLayout):
            raise TypeError('Dashboard card content layout must be a QLayout')
        self.viewLayout.addLayout(layout, stretch)
        self.contentWidget.show()

    def isChecked(self):
        return self.switchButton.isChecked()

    def setChecked(self, checked):
        self.switchButton.setChecked(bool(checked))

    def setSwitchVisible(self, visible):
        self.switchButton.setVisible(bool(visible))

    def setCardBackgroundColor(self, light, dark=None):
        """Theme-aware card fill; one supplied color applies to both themes."""
        lightColor = QColor(light)
        darkColor = QColor(light if dark is None else dark)
        if not lightColor.isValid() or not darkColor.isValid():
            raise ValueError('Invalid dashboard card background color')
        self._lightBackground, self._darkBackground = lightColor, darkColor
        self.backgroundColorAni.stop()
        self.setBackgroundColor(self._normalBackgroundColor())

    def resetCardBackgroundColor(self):
        """Restore SimpleCardWidget's original translucent theme background."""
        self._lightBackground = QColor()
        self._darkBackground = QColor()
        self.backgroundColorAni.stop()
        self.setBackgroundColor(self._normalBackgroundColor())

    def _normalBackgroundColor(self):
        color = self._darkBackground if isDarkTheme() else self._lightBackground
        return QColor(color) if color.isValid() else super()._normalBackgroundColor()

    checked = Property(bool, isChecked, setChecked, notify=checkedChanged)
