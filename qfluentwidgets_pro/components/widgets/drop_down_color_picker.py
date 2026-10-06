# coding:utf-8
"""A lightweight HSV/RGBA flyout editor with explicit draft confirmation."""

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, QRegularExpression, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIntValidator, QLinearGradient, QPainter, QPainterPath, QPen, QRegularExpressionValidator
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from ...common.config import qconfig
from ...common.icon import FluentIcon
from ...common.style_sheet import isDarkTheme
from .button import DropDownPushButton, PushButton, TransparentToolButton
from .combo_box import ComboBox
from .drop_down_color_palette import _PaletteFlyout, _drawColor, _validColor
from .flyout import FlyoutAnimationType, FlyoutViewBase
from .label import BodyLabel
from .line_edit import LineEdit
from .scroll_area import ScrollArea
from .slider import Slider


class _HueSaturationPanel(QWidget):
    positionChanged = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(288, 288)
        self.hue, self.saturation = 0., 1.
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(self.tr('Hue and saturation'))
        self.setCursor(Qt.CrossCursor)

    def setPosition(self, hue, saturation):
        self.hue, self.saturation = hue, saturation
        self.update()

    def _pick(self, position):
        hue = max(0., min(1., position.x() / (self.width() - 1)))
        saturation = 1 - max(0., min(1., position.y() / (self.height() - 1)))
        self.setPosition(hue, saturation)
        self.positionChanged.emit(hue, saturation)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setFocus(Qt.MouseFocusReason)
            self._pick(event.position())
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._pick(event.position())
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        dx = {Qt.Key_Left: -1, Qt.Key_Right: 1}.get(event.key(), 0)
        dy = {Qt.Key_Up: -1, Qt.Key_Down: 1}.get(event.key(), 0)
        if dx or dy:
            self._pick(QPointF(self.hue * (self.width() - 1) + dx,
                              (1 - self.saturation) * (self.height() - 1) + dy))
            event.accept()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        clip = QPainterPath()
        clip.addRoundedRect(rect, 5, 5)
        painter.setClipPath(clip)
        hue = QLinearGradient(0, 0, self.width() - 1, 0)
        for stop in range(7):
            hue.setColorAt(stop / 6, QColor.fromHsvF(stop / 6, 1, 1))
        painter.fillRect(rect, hue)
        saturation = QLinearGradient(0, 0, 0, self.height() - 1)
        saturation.setColorAt(0, QColor(255, 255, 255, 0))
        saturation.setColorAt(1, QColor(255, 255, 255))
        painter.fillRect(rect, saturation)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(0, 0, 0, 22), 1))
        painter.drawRoundedRect(rect, 5, 5)
        painter.setPen(QPen(Qt.black, 2.5))
        painter.drawEllipse(QPointF(self.hue * (self.width() - 1),
                                   (1 - self.saturation) * (self.height() - 1)), 8, 8)


class _ColorSlider(Slider):
    """Reuse Fluent's animated handle and keyboard behavior over a color gradient."""

    def __init__(self, parent):
        super().__init__(Qt.Horizontal, parent)
        self.setRange(0, 255)
        self.setFixedHeight(22)
        self.stops = (QColor('black'), QColor('white'))
        self.checkerboard = False

    def setColors(self, stops, handle, checkerboard=False):
        self.stops = tuple(QColor(color) for color in stops)
        self.checkerboard = checkerboard
        self.handle.setHandleColor(handle, handle)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            super().mousePressEvent(event)
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            super().mouseMoveEvent(event)
            event.accept()
        else:
            event.ignore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 5, self.width(), 12)
        clip = QPainterPath()
        clip.addRoundedRect(rect, 6, 6)
        painter.setClipPath(clip)
        if self.checkerboard:
            shades = ('#808080', '#DCDCDC')
            for row in range(3):
                for column in range((self.width() + 3) // 4):
                    painter.fillRect(column * 4, 5 + row * 4, 4, 4,
                                     QColor(shades[(row + column) % 2]))
        gradient = QLinearGradient(11, 0, max(12, self.width() - 11), 0)
        for index, color in enumerate(self.stops):
            gradient.setColorAt(index / (len(self.stops) - 1), color)
        painter.fillRect(rect, gradient)


class _ColorPickerView(FlyoutViewBase):
    confirmed = Signal(QColor)
    cancelled = Signal()
    previewed = Signal(QColor)

    def __init__(self, color, enableAlpha=True, parent=None):
        super().__init__(parent)
        self._updating, self._enableAlpha = False, enableAlpha
        self._hue, self._saturation, self._value = 0., 0., 0.
        self._color = QColor('black')
        self.setFixedWidth(320)
        self.body = QWidget(self)
        self.body.setFixedSize(318, 566 if enableAlpha else 526)
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setWidget(self.body)
        self.scrollArea.setWidgetResizable(False)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.enableTransparentBackground()
        self.huePanel = _HueSaturationPanel(self.body)
        self.huePanel.move(15, 15)
        self.brightnessSlider = _ColorSlider(self.body)
        self.brightnessSlider.setGeometry(15, 319, 288, 22)
        self.brightnessSlider.setAccessibleName(self.tr('Brightness'))
        self.modeComboBox = ComboBox(self.body)
        self.modeComboBox.addItems(['RGB', 'HSV'])
        self.modeComboBox.setGeometry(15, 351, 92, 32)
        self.modeComboBox.setAccessibleName(self.tr('Color model'))
        self.hexEdit = LineEdit(self.body)
        self.hexEdit.setGeometry(167, 351, 136, 32)
        self.hexEdit.setAccessibleName(self.tr('Hexadecimal color, AARRGGBB or RRGGBB'))
        self.hexEdit.setValidator(QRegularExpressionValidator(
            QRegularExpression('#?(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})'), self.hexEdit))
        self.labels, self.edits, self.sliders = [], [], []
        for index, name in enumerate('RGBA'):
            y = 395 + index * 40
            label = BodyLabel(name, self.body)
            label.setGeometry(15, y, 16, 32)
            edit = LineEdit(self.body)
            edit.setGeometry(31, y, 64, 32)
            edit.setValidator(QIntValidator(0, 255, edit))
            slider = _ColorSlider(self.body)
            slider.setGeometry(103, y + 5, 200, 22)
            edit.textEdited.connect(lambda text, i=index: self._editChannel(i, text))
            edit.editingFinished.connect(lambda i=index: self._restoreEdit(i))
            slider.valueChanged.connect(lambda value, i=index: self._channelChanged(i, value))
            self.labels.append(label)
            self.edits.append(edit)
            self.sliders.append(slider)
            if index == 3 and not enableAlpha:
                for widget in (label, edit, slider):
                    widget.hide()
        self.buttonBar = QWidget(self)
        self.buttonBar.setFixedHeight(40)
        footer = QHBoxLayout(self.buttonBar)
        footer.setContentsMargins(4, 4, 4, 4)
        footer.setSpacing(0)
        self.yesButton = TransparentToolButton(FluentIcon.ACCEPT, self.buttonBar)
        self.cancelButton = TransparentToolButton(FluentIcon.CLOSE, self.buttonBar)
        for button, name in ((self.yesButton, self.tr('Confirm')), (self.cancelButton, self.tr('Cancel'))):
            button.setIconSize(QSize(16, 16))
            button.setAccessibleName(name)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            footer.addWidget(button, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.scrollArea, 1)
        layout.addWidget(self.buttonBar)
        self.setFixedHeight(608 if enableAlpha else 568)
        self.huePanel.positionChanged.connect(self._panelChanged)
        self.brightnessSlider.valueChanged.connect(self._brightnessChanged)
        self.modeComboBox.currentIndexChanged.connect(self._sync)
        self.hexEdit.textEdited.connect(self._hexEdited)
        self.hexEdit.editingFinished.connect(self._restoreHex)
        self.yesButton.clicked.connect(self.confirm)
        self.cancelButton.clicked.connect(self.cancelled)
        self.hexEdit.returnPressed.connect(self.confirm)
        for edit in self.edits:
            edit.returnPressed.connect(self.confirm)
        # Child controls retain their arrows/typing; Escape always cancels this
        # editor. Nested combo/context menus receive their own Escape first.
        for widget in (self.huePanel, self.brightnessSlider, self.modeComboBox,
                       self.hexEdit, *self.edits, *self.sliders, self.yesButton, self.cancelButton):
            widget.installEventFilter(self)
        self.setColor(color)

    def color(self):
        return QColor(self._color)

    def setColor(self, color):
        self._setDraft(_validColor(color), preview=False)

    def _setDraft(self, color, preserveHSV=False, exclude=None, preview=True):
        color = QColor.fromRgba(color.rgba())
        if not self._enableAlpha:
            color.setAlpha(255)
        changed = self._color != color
        self._color = color
        if not preserveHSV:
            if color.hsvHueF() >= 0:
                self._hue = color.hsvHueF()
            self._saturation, self._value = color.saturationF(), color.valueF()
        self._sync(exclude=exclude)
        if changed and preview:
            self.previewed.emit(self.color())

    def _hsvColor(self):
        return QColor.fromHsvF(self._hue, self._saturation, self._value, self._color.alphaF())

    def _panelChanged(self, hue, saturation):
        self._hue, self._saturation = hue, saturation
        self._setDraft(self._hsvColor(), preserveHSV=True)

    def _brightnessChanged(self, value):
        if not self._updating:
            self._value = value / 255
            self._setDraft(self._hsvColor(), preserveHSV=True)

    def _channelValues(self):
        if self.modeComboBox.currentIndex() == 0:
            return (self._color.red(), self._color.green(), self._color.blue(), self._color.alpha())
        return (min(359, round(self._hue * 360)), round(self._saturation * 100),
                round(self._value * 100), self._color.alpha())

    def _channelChanged(self, index, value, exclude=None):
        if self._updating:
            return
        color = self.color()
        preserve = False
        if index == 3:
            color.setAlpha(value)
            preserve = True
        elif self.modeComboBox.currentIndex() == 0:
            (color.setRed, color.setGreen, color.setBlue)[index](value)
        else:
            if index == 0:
                self._hue = value / 360
            elif index == 1:
                self._saturation = value / 100
            else:
                self._value = value / 100
            color, preserve = self._hsvColor(), True
        self._setDraft(color, preserve, exclude)

    def _editChannel(self, index, text):
        edit = self.edits[index]
        if edit.hasAcceptableInput():
            edit.setError(False)
            self._channelChanged(index, int(text), exclude=edit)

    def _restoreEdit(self, index):
        self.edits[index].setText(str(self._channelValues()[index]))

    def _hexEdited(self, text):
        if self.hexEdit.hasAcceptableInput():
            digits = text.lstrip('#')
            color = QColor('#' + digits)
            if len(digits) == 6:
                color.setAlpha(self._color.alpha())
            self.hexEdit.setError(False)
            self._setDraft(color, exclude=self.hexEdit)

    def _restoreHex(self):
        self.hexEdit.setText(self._color.name(QColor.HexArgb if self._enableAlpha else QColor.HexRgb))
        self.hexEdit.setError(False)

    def _sync(self, index=None, exclude=None):
        self._updating = True
        try:
            self.huePanel.setPosition(self._hue, self._saturation)
            self.brightnessSlider.setValue(round(self._value * 255))
            full = QColor.fromHsvF(self._hue, self._saturation, 1)
            handle = self.color()
            handle.setAlpha(255)
            self.brightnessSlider.setColors((QColor('black'), full), handle)
            values = self._channelValues()
            rgb = self.modeComboBox.currentIndex() == 0
            for channel in range(4):
                maximum = 255 if rgb or channel == 3 else (359 if channel == 0 else 100)
                self.labels[channel].setText(('RGBA' if rgb else 'HSVA')[channel])
                name = ('RGBA' if rgb else 'HSVA')[channel]
                self.edits[channel].setAccessibleName(self.tr('%1 value').replace('%1', name))
                self.sliders[channel].setAccessibleName(self.tr('%1 slider').replace('%1', name))
                self.edits[channel].validator().setRange(0, maximum)
                if self.edits[channel] is not exclude:
                    self.edits[channel].setText(str(values[channel]))
                self.sliders[channel].setRange(0, maximum)
                self.sliders[channel].setValue(values[channel])
                if channel == 3:
                    transparent, opaque = QColor(handle), QColor(handle)
                    transparent.setAlpha(0)
                    stops = (transparent, opaque)
                elif rgb:
                    low, high = QColor(handle), QColor(handle)
                    setter = ('setRed', 'setGreen', 'setBlue')[channel]
                    getattr(low, setter)(0)
                    getattr(high, setter)(255)
                    stops = (low, high)
                elif channel == 0:
                    stops = tuple(QColor.fromHsvF(i / 6, self._saturation, self._value) for i in range(7))
                elif channel == 1:
                    stops = (QColor.fromHsvF(self._hue, 0, self._value),
                             QColor.fromHsvF(self._hue, 1, self._value))
                else:
                    stops = (QColor('black'), full)
                self.sliders[channel].setColors(stops, handle, channel == 3)
            if self.hexEdit is not exclude:
                self._restoreHex()
        finally:
            self._updating = False

    def confirm(self):
        for edit in (self.hexEdit, *self.edits[:4 if self._enableAlpha else 3]):
            if not edit.hasAcceptableInput():
                edit.setError(True)
                edit.setFocus()
                return
        self.confirmed.emit(self.color())

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.cancelled.emit()
            return True
        if watched is self.modeComboBox and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_Down):
                self.modeComboBox._toggleComboMenu()
                return True
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        color = QColor(255, 255, 255, 15) if isDarkTheme() else QColor(0, 0, 0, 17)
        painter.fillRect(1, self.buttonBar.y(), self.width() - 2, 1, color)


class DropDownColorPicker(DropDownPushButton):
    """HSV/RGBA flyout editor. Only confirmation changes the committed color.

    Alpha editing defaults to enabled. Hex uses AARRGGBB; six-digit RGB input
    preserves the current alpha. Disabling alpha normalizes the color to opaque.
    Choosing any color is independent of the application's theme accent.
    """

    colorChanged = Signal(QColor)
    colorSelected = Signal(QColor)
    colorPreviewed = Signal(QColor)
    pickingCanceled = Signal()

    def __init__(self, color='#0078D4', parent=None, enableAlpha=True):
        if isinstance(color, QWidget) and parent is None:
            parent, color = color, '#0078D4'
        super().__init__(parent=parent)
        self._enableAlpha = bool(enableAlpha)
        self._color = QColor('black')
        self._flyout, self._confirmed = None, False
        self.setColor(color)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAccessibleName(self.tr('Color picker'))
        self.clicked.connect(self.showPicker)
        qconfig.themeChangedFinished.connect(self._refreshTheme)

    def color(self):
        return QColor(self._color)

    def setColor(self, color):
        color = _validColor(color)
        color = QColor.fromRgba(color.rgba())
        if not self._enableAlpha:
            color.setAlpha(255)
        changed = self._color != color
        self._color = color
        self.update()
        if self._flyout:
            self._flyout.view.setColor(self._color)
        if changed:
            self.colorChanged.emit(self.color())

    def setAlphaEnabled(self, enabled):
        enabled = bool(enabled)
        if enabled != self._enableAlpha:
            self.closePicker()
            self._enableAlpha = enabled
            self.setColor(self._color)

    def isAlphaEnabled(self):
        return self._enableAlpha

    def showPicker(self):
        if not self.isEnabled():
            return
        if self._flyout:
            self.closePicker()
            return
        self._confirmed = False
        view = _ColorPickerView(self._color, self._enableAlpha)
        flyout = _PaletteFlyout(view, self.window())
        self._flyout = flyout
        flyout.closed.connect(self._onClosed)
        view.confirmed.connect(self._onConfirmed)
        view.cancelled.connect(self.closePicker)
        view.previewed.connect(self.colorPreviewed)
        # Leave room for shadow margins and pin the footer within the actual
        # button's monitor, even on small/high-DPI displays.
        bounds = self.screen().availableGeometry()
        view.setFixedHeight(min(view.height(), max(180, bounds.height() - 36)))
        flyout.adjustSize()
        flyout.exec(self.mapToGlobal(QPoint(self.width() // 2 - flyout.sizeHint().width() // 2,
                                           self.height())), FlyoutAnimationType.DROP_DOWN)
        view.huePanel.setFocus(Qt.PopupFocusReason)

    def closePicker(self):
        if self._flyout:
            self._flyout.close()

    def _onConfirmed(self, color):
        self._confirmed = True
        self.closePicker()
        self.setColor(color)
        self.colorSelected.emit(self.color())

    def _onClosed(self):
        self._flyout = None
        self.setDown(False)
        if self.isVisible() and self.isEnabled():
            self.setFocus(Qt.PopupFocusReason)
        if not self._confirmed:
            self.pickingCanceled.emit()

    def _refreshTheme(self):
        self.update()
        if self._flyout:
            view = self._flyout.view
            view.update()
            view.huePanel.update()
            view.brightnessSlider.update()
            view.brightnessSlider.handle.update()
            for slider in view.sliders:
                slider.update()
                slider.handle.update()
            self._flyout.setShadowEffect()

    def mouseReleaseEvent(self, event):
        PushButton.mouseReleaseEvent(self, event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Down) and self.isEnabled():
            if not event.isAutoRepeat():
                self.showPicker()
            event.accept()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        self.closePicker()
        super().hideEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.EnabledChange and not self.isEnabled():
            self.closePicker()
        super().changeEvent(event)

    def sizeHint(self):
        return QSize(54, 32)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(.3628)
        elif self.isDown():
            painter.setOpacity(.786)
        _drawColor(painter, QRectF(4, (self.height() - 22) / 2, 22, 22), self._color)
