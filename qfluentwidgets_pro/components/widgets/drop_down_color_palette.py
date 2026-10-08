# coding:utf-8
"""Compact Office-style color palette; selecting colors never changes the accent."""

from PySide6.QtCore import QEvent, QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QDialog, QSizePolicy, QWidget

from ...common.config import qconfig
from ...common.font import getFont
from ...common.icon import FluentIcon, drawIcon
from ...common.style_sheet import isDarkTheme
from .button import DropDownPushButton, PushButton
from .flyout import Flyout, FlyoutAnimationType, FlyoutViewBase


def _validColor(value):
    try:
        color = QColor(value)
    except (TypeError, ValueError):
        raise ValueError('Invalid color: %r' % (value,)) from None
    if not color.isValid():
        raise ValueError('Invalid color: %r' % (value,))
    return color


def _drawColor(painter, rect, color):
    if color.alpha() < 255:
        path = QPainterPath()
        path.addRoundedRect(rect, 4, 4)
        painter.save()
        painter.setClipPath(path)
        shades = ('#555555', '#777777') if isDarkTheme() else ('#FFFFFF', '#DDDDDD')
        for row in range(int(rect.height() / 4) + 1):
            for column in range(int(rect.width() / 4) + 1):
                painter.fillRect(QRectF(rect.x() + column * 4, rect.y() + row * 4, 4, 4),
                                 QColor(shades[(row + column) % 2]))
        painter.restore()
    painter.setPen(Qt.NoPen)
    painter.setBrush(color)
    painter.drawRoundedRect(rect, 4, 4)


class _PaletteButton(QAbstractButton):
    def __init__(self, view, color=None, text='', icon=None):
        super().__init__(view)
        self.view, self.color, self.icon = view, QColor(color) if color is not None else None, icon
        self.selected = False
        self._hovered = False
        self._showFocus = False
        self.setText(text)
        self.setFont(getFont(14))
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName(text or self.color.name(QColor.HexArgb))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.window().close()
            event.accept()
        elif self.view.navigate(self, event.key()):
            event.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.click()
            event.accept()
        else:
            super().keyPressEvent(event)

    def enterEvent(self, event):
        self._hovered = True
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        super().leaveEvent(event)
        self.update()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._showFocus = event.reason() in (Qt.TabFocusReason, Qt.BacktabFocusReason, Qt.OtherFocusReason)
        self.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        foreground = QColor('#FFFFFF' if isDarkTheme() else '#000000')
        if self.text():
            if self._hovered or self.isDown() or (self.hasFocus() and self._showFocus):
                shade = 255 if isDarkTheme() else 0
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(shade, shade, shade, 22 if self.isDown() else 12))
                row = QPainterPath()
                row.setFillRule(Qt.WindingFill)
                row.addRoundedRect(QRectF(self.rect()), 8, 8)
                # Round only the panel-facing corners; the separator edge is square.
                row.addRect(QRectF(0, 8 if self.color is not None else 0,
                                  self.width(), self.height() - 8))
                painter.drawPath(row)
            if self.color is not None:
                _drawColor(painter, QRectF(11, 7, 28, 28), self.color)
            elif self.icon:
                drawIcon(self.icon, painter, QRectF(15, 11, 20, 20))
            painter.setPen(foreground)
            painter.setFont(self.font())
            painter.drawText(QRectF(51, 0, self.width() - 63, self.height()),
                             Qt.AlignLeft | Qt.AlignVCenter, self.text())
        else:
            outlined = (self.selected or self._hovered or
                        (self.hasFocus() and self._showFocus) or self.isDown())
            bounds = QRectF(self.rect())
            _drawColor(painter, bounds.adjusted(2, 2, -2, -2) if outlined else bounds, self.color)
            if outlined:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(Qt.white, 1.5 if self.selected else 1))
                inset = .75 if self.selected else .5
                painter.drawRoundedRect(bounds.adjusted(inset, inset, -inset, -inset), 4, 4)


class _PaletteView(FlyoutViewBase):
    colorSelected = Signal(QColor, bool)
    moreColorsRequested = Signal()

    def __init__(self, picker):
        super().__init__()
        self.setFixedSize(340, 432)
        self.setFont(getFont(14))
        self.automaticButton = _PaletteButton(self, picker.automaticColor(), self.tr('Automatic'))
        self.automaticButton.setGeometry(1, 0, 338, 42)
        self.automaticButton.clicked.connect(
            lambda: self.colorSelected.emit(QColor(self.automaticButton.color), True))
        self.buttons = []
        for row, colors in enumerate(picker.THEME_COLORS + (picker.STANDARD_COLORS,)):
            y = 88 if row == 0 else (128 + (row - 1) * 32 if row < 6 else 344)
            for column, color in enumerate(colors):
                button = _PaletteButton(self, color)
                button.setGeometry(12 + column * 32, y, 28, 28)
                button.clicked.connect(lambda checked=False, b=button:
                                       self.colorSelected.emit(QColor(b.color), False))
                self.buttons.append(button)
        self.moreButton = _PaletteButton(self, text=self.tr('More Colors...'), icon=FluentIcon.PALETTE)
        self.moreButton.setGeometry(1, 390, 338, 42)
        self.moreButton.clicked.connect(self.moreColorsRequested)
        self.setSelection(picker.color(), picker.isAutomatic())

    def setSelection(self, color, automatic):
        for button in self.buttons:
            button.selected = not automatic and button.color == color
            button.update()

    def navigate(self, button, key):
        if key not in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down, Qt.Key_Home, Qt.Key_End):
            return False
        if button in self.buttons:
            index = self.buttons.index(button)
            column = index % 10
            horizontal = -1 if key == Qt.Key_Left else 1
            if self.layoutDirection() == Qt.RightToLeft:
                horizontal = -horizontal
            if key in (Qt.Key_Left, Qt.Key_Right):
                target = self.buttons[index - column + (column + horizontal) % 10]
            elif key == Qt.Key_Home:
                target = self.buttons[index - column]
            elif key == Qt.Key_End:
                target = self.buttons[index - column + 9]
            elif key == Qt.Key_Up:
                target = self.buttons[index - 10] if index >= 10 else self.automaticButton
            else:
                target = self.buttons[index + 10] if index < 60 else self.moreButton
        else:
            target = self.buttons[0 if button is self.automaticButton else 60]
        target.setFocus(Qt.OtherFocusReason)
        return True

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        separator = QColor(255, 255, 255, 22) if isDarkTheme() else QColor(0, 0, 0, 18)
        for y in (42, 300, 389):
            painter.fillRect(1, y, self.width() - 2, 1, separator)
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        painter.setFont(self.font())
        painter.drawText(QRectF(12, 43, 316, 40), Qt.AlignLeft | Qt.AlignVCenter, self.tr('Theme Colors'))
        painter.drawText(QRectF(12, 301, 316, 40), Qt.AlignLeft | Qt.AlignVCenter, self.tr('Standard Colors'))


class _PaletteFlyout(Flyout):
    def __init__(self, *args, **kwargs):
        self._closing = False
        super().__init__(*args, **kwargs)

    def closeEvent(self, event):
        self._closing = True
        if self.aniManager:
            self.aniManager.aniGroup.stop()
        super().closeEvent(event)

    def hideEvent(self, event):
        super().hideEvent(event)
        # Native Qt.Popup dismissal can hide instead of sending a close event.
        if not self._closing:
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            event.accept()
        else:
            super().keyPressEvent(event)


class DropDownColorPalette(DropDownPushButton):
    """A 54x32 button with 60 theme swatches, ten standard colors and ColorDialog.

    `colorChanged` reports actual changes; `colorSelected` reports every user
    confirmation. Automatic is an explicit, configurable color (black by default),
    not the application's accent. All dimensions are logical pixels.
    """

    colorChanged = Signal(QColor)
    colorSelected = Signal(QColor)
    automaticChanged = Signal(bool)

    THEME_COLORS = (
        ('#FFFFFF', '#000000', '#E7E6E6', '#44546A', '#4472C4', '#4472C4', '#A5A5A5', '#FFC000', '#5B9BD5', '#70AD47'),
        ('#F2F2F2', '#808080', '#D0CECE', '#D6DCE5', '#DAE3F3', '#FBE5D6', '#EDEDED', '#FFF2CC', '#DEEBF7', '#E2F0D9'),
        ('#D9D9D9', '#595959', '#AFABAB', '#ADB9CA', '#B4C7E7', '#F8CBAD', '#DBDBDB', '#FFE699', '#BDD7EE', '#C5E0B4'),
        ('#BFBFBF', '#404040', '#767171', '#8497B0', '#8FAADC', '#F4B183', '#C9C9C9', '#FFD966', '#9DC3E6', '#A9D18E'),
        ('#A6A6A6', '#262626', '#3B3838', '#333F50', '#2F5597', '#C55A11', '#7C7C7C', '#BF9000', '#2E75B6', '#548235'),
        ('#808080', '#0D0D0D', '#181717', '#222A35', '#203864', '#843C0B', '#525252', '#806000', '#1F4E79', '#385624'),
    )
    STANDARD_COLORS = ('#C00000', '#FF0000', '#FFC000', '#FFFF00', '#92D050', '#00B050', '#00B0F0', '#0070C0', '#002060', '#7030A0')

    def __init__(self, color='#0078D4', parent=None):
        if isinstance(color, QWidget) and parent is None:
            parent, color = color, '#0078D4'
        super().__init__(parent=parent)
        self._color, self._automaticColor = _validColor(color), QColor('#000000')
        self._automatic, self._enableAlpha = False, False
        self._flyout, self._dialog = None, None
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAccessibleName(self.tr('Color palette'))
        self.clicked.connect(self.showPalette)
        qconfig.themeChangedFinished.connect(self._refreshTheme)

    def color(self):
        return QColor(self._color)

    def setColor(self, color):
        self._setColor(_validColor(color), False)

    def automaticColor(self):
        return QColor(self._automaticColor)

    def setAutomaticColor(self, color):
        self._automaticColor = _validColor(color)
        if self._automatic:
            self._setColor(self._automaticColor, True)
        if self._flyout:
            self._flyout.view.automaticButton.color = self.automaticColor()
            self._flyout.view.automaticButton.update()

    def isAutomatic(self):
        return self._automatic

    def setAutomatic(self):
        self._setColor(self._automaticColor, True)

    def setAlphaEnabled(self, enabled):
        self._enableAlpha = bool(enabled)

    def isAlphaEnabled(self):
        return self._enableAlpha

    def _setColor(self, color, automatic):
        changed, modeChanged = self._color != color, self._automatic != automatic
        self._color, self._automatic = QColor(color), automatic
        self.update()
        if self._flyout:
            self._flyout.view.setSelection(self._color, automatic)
        if modeChanged:
            self.automaticChanged.emit(automatic)
        if changed:
            self.colorChanged.emit(self.color())

    def _chooseColor(self, color, automatic=False):
        self.closePalette()
        self._setColor(color, automatic)
        self.colorSelected.emit(self.color())

    def showPalette(self):
        if not self.isEnabled() or self._dialog:
            return
        if self._flyout:
            self.closePalette()
            return
        view = _PaletteView(self)
        view.setLayoutDirection(self.layoutDirection())
        flyout = _PaletteFlyout(view, self.window())
        self._flyout = flyout
        flyout.closed.connect(self._onPaletteClosed)
        view.colorSelected.connect(self._chooseColor)
        view.moreColorsRequested.connect(self.showColorDialog)
        flyout.show()
        position = self.mapToGlobal(QPoint(self.width() // 2 - flyout.sizeHint().width() // 2,
                                          self.height()))
        flyout.exec(position, FlyoutAnimationType.DROP_DOWN)
        next((button for button in view.buttons if button.selected), view.automaticButton).setFocus(Qt.PopupFocusReason)

    def closePalette(self):
        if self._flyout:
            self._flyout.close()

    def _onPaletteClosed(self):
        self._flyout = None
        self.setDown(False)
        if self.isVisible() and self.isEnabled():
            self.setFocus(Qt.PopupFocusReason)

    def showColorDialog(self):
        if not self.isEnabled() or self._dialog:
            return
        self.closePalette()
        # Lazy to avoid the widgets <-> dialog_box package import cycle.
        from ..dialog_box.color_dialog import ColorDialog
        self._dialog = ColorDialog(self.color(), self.tr('Choose Color'), self.window(), self._enableAlpha)
        self._dialog.setAttribute(Qt.WA_DeleteOnClose)
        self._dialog.finished.connect(self._onDialogFinished)
        self._dialog.open()

    def _onDialogFinished(self, result):
        dialog, self._dialog = self._dialog, None
        if dialog is not None and result == QDialog.Accepted:
            # ColorDialog edits 8-bit RGBA but its HSV sliders can change QColor's
            # internal specification/precision without changing those channels.
            self._chooseColor(QColor.fromRgba(dialog.color.rgba()))

    def _refreshTheme(self):
        self.update()
        if self._flyout:
            self._flyout.view.update()
            for child in self._flyout.view.findChildren(_PaletteButton):
                child.update()
            self._flyout.setShadowEffect()

    def mouseReleaseEvent(self, event):
        # DropDownPushButton opens a menu unconditionally on release; use clicked
        # instead, so right clicks and canceled presses do not open the palette.
        PushButton.mouseReleaseEvent(self, event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Down) and self.isEnabled():
            if not event.isAutoRepeat():
                self.showPalette()
            event.accept()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        self.closePalette()
        if self._dialog:
            self._dialog.reject()
        super().hideEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.EnabledChange and not self.isEnabled():
            self.closePalette()
            if self._dialog:
                self._dialog.reject()
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
