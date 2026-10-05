"""Calendar plus the existing time wheels, with one atomic confirmation."""
from PySide6.QtCore import QDate, QDateTime, QEvent, QPoint, Property, QRectF, Qt, QTime, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from ...common.icon import FluentIcon
from ...common.color import autoFallbackThemeColor
from ...common.style_sheet import isDarkTheme, setCustomStyleSheet
from ..widgets.button import TransparentToolButton
from ..widgets.flyout import Flyout, FlyoutAnimationType, FlyoutViewBase
from .calendar_picker import CalendarPicker, FastCalendarPicker
from .calendar_view import CalendarView
from .fast_calendar_view import FastCalendarView
from .picker_base import ItemMaskWidget, PickerPanel, SeparatorWidget


class _EmbeddedCalendarMixin:
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)
        self.stackedWidget.setGraphicsEffect(None)
        for view in (self.dayView, self.monthView, self.yearView):
            qss = 'CalendarViewBase {border: none; border-radius: 0; background: transparent;}'
            setCustomStyleSheet(view, qss, qss)

    def _onDayItemClicked(self, date):
        if isinstance(date, QDate) and date.isValid() and date != self.date:
            self.setDate(date)
            self.dateChanged.emit(QDate(date))

    def _onResetted(self):
        self.resetted.emit()

    def paintEvent(self, event):
        # The combined view paints the one shared background and outer border.
        pass


class _EmbeddedCalendar(_EmbeddedCalendarMixin, CalendarView):
    pass


class _EmbeddedFastCalendar(_EmbeddedCalendarMixin, FastCalendarView):
    pass


class _EmbeddedTimeMask(ItemMaskWidget):
    def paintEvent(self, event):
        # PickerPanel's original mask assumes its standalone popup margins.
        # Map actual viewport rows instead, including while the wheels animate.
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(autoFallbackThemeColor(self.lightBackgroundColor, self.darkBackgroundColor))
        painter.drawRoundedRect(self.rect().adjusted(4, 0, -3, 0), 5, 5)
        painter.setPen(Qt.black if isDarkTheme() else Qt.white)
        painter.setFont(self.font())
        for column in self.listWidgets:
            viewport = column.viewport()
            top = viewport.mapFromGlobal(self.mapToGlobal(QPoint(0, 0))).y()
            seen = set()
            for y in (top, top + self.height() - 1):
                item = column.itemAt(QPoint(viewport.width() // 2, y))
                if item is None or column.row(item) in seen:
                    continue
                seen.add(column.row(item))
                pos = self.mapFromGlobal(viewport.mapToGlobal(column.visualItemRect(item).topLeft()))
                painter.save()
                painter.translate(pos)
                self._drawText(item, painter, 0)
                painter.restore()


class _EmbeddedTimePanel(PickerPanel):
    def __init__(self, parent=None, showSeconds=True):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.view.setGraphicsEffect(None)
        self.view.setObjectName('calendarTimeWheels')
        self.itemMaskWidget.hide()
        self.itemMaskWidget.deleteLater()
        self.itemMaskWidget = _EmbeddedTimeMask(self.listWidgets, self)
        self.hBoxLayout.setContentsMargins(9, 11, 9, 11)
        self.hBoxLayout.setSpacing(0)
        self.listLayout.setSpacing(0)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(0)
        for button in (self.yesButton, self.cancelButton, self.resetButton):
            button.hide()
        self.hSeparatorWidget.hide()
        width = 80 if showSeconds else 120
        self.addColumn(range(24), width)
        self.addColumn(range(60), width)
        if showSeconds:
            self.addColumn(range(60), width)
        self.itemMaskWidget.setAttribute(Qt.WA_TransparentForMouseEvents)


class _CalendarTimeView(FlyoutViewBase):
    confirmed = Signal(QDateTime)
    cancelled = Signal()
    resetted = Signal()

    def __init__(self, dateTime, fast=False, showSeconds=True, parent=None):
        super().__init__(parent)
        self._initial = QDateTime(dateTime)
        self.calendarView = (_EmbeddedFastCalendar if fast else _EmbeddedCalendar)(self)
        self.timePanel = _EmbeddedTimePanel(self, showSeconds)
        self.calendarView.setDate(dateTime.date())
        time = dateTime.time()
        values = [str(time.hour()), str(time.minute())]
        if showSeconds:
            values.append(str(time.second()))
        self.timePanel.setValue(values)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(1, 1, 1, 1)
        self.vBoxLayout.setSpacing(0)
        self.bodyLayout = QHBoxLayout()
        self.bodyLayout.setContentsMargins(0, 0, 0, 0)
        self.bodyLayout.setSpacing(0)
        self.bodyLayout.addWidget(self.calendarView)
        self.bodyLayout.addWidget(SeparatorWidget(Qt.Vertical, self))
        self.bodyLayout.addWidget(self.timePanel)
        self.vBoxLayout.addLayout(self.bodyLayout)
        self.vBoxLayout.addWidget(SeparatorWidget(Qt.Horizontal, self))
        self.buttonBar = QWidget(self)
        self.buttonBar.setFixedHeight(36)
        self.buttonLayout = QHBoxLayout(self.buttonBar)
        self.buttonLayout.setContentsMargins(3, 3, 3, 3)
        self.buttonLayout.setSpacing(0)
        self.yesButton = TransparentToolButton(FluentIcon.ACCEPT, self.buttonBar)
        self.cancelButton = TransparentToolButton(FluentIcon.CLOSE, self.buttonBar)
        for button, name in ((self.yesButton, self.tr('Confirm')),
                             (self.cancelButton, self.tr('Cancel'))):
            button.setAccessibleName(name)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.buttonLayout.addWidget(button, 1)
        self.vBoxLayout.addWidget(self.buttonBar)
        self.yesButton.clicked.connect(lambda: self.confirmed.emit(self.dateTime()))
        self.cancelButton.clicked.connect(self.cancelled)
        self.calendarView.resetted.connect(self.resetted)

    def dateTime(self):
        values = [int(v) for v in self.timePanel.value()]
        result = QDateTime(self._initial)
        result.setDate(self.calendarView.date)
        result.setTime(QTime(*values) if len(values) == 3 else QTime(*values, 0))
        return result

    def showEvent(self, event):
        QApplication.instance().installEventFilter(self)
        super().showEvent(event)

    def hideEvent(self, event):
        QApplication.instance().removeEventFilter(self)
        super().hideEvent(event)

    def eventFilter(self, watched, event):
        if self.isVisible():
            if event.type() == QEvent.MouseButtonPress:
                if not self.rect().contains(self.mapFromGlobal(event.globalPosition().toPoint())):
                    self.window().close()
                    return True
            elif event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self.cancelled.emit()
                    return True
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    self.confirmed.emit(self.dateTime())
                    return True
        return super().eventFilter(watched, event)


class _CalendarTimePickerMixin:
    dateTimeChanged = Signal(QDateTime)
    timeChanged = Signal(QTime)

    def __init__(self, parent=None, showSeconds=True):
        super().__init__(parent)
        self._dateTime = QDateTime()
        self._showSeconds = bool(showSeconds)
        self._dateTimeFormat = 'yyyy-MM-dd HH:mm:ss' if showSeconds else 'yyyy-MM-dd HH:mm'
        self._dateFormat = self._dateTimeFormat
        self.flyoutAnimationType = FlyoutAnimationType.DROP_DOWN
        self._calendarTimeView = None
        self._flyout = None
        self.setText(self.tr('Pick a date and time'))

    def getDateTime(self):
        return QDateTime(self._dateTime)

    def setDateTime(self, dateTime):
        if not isinstance(dateTime, QDateTime):
            raise TypeError('dateTime must be a QDateTime')
        if dateTime == self._dateTime and dateTime.timeZone() == self._dateTime.timeZone():
            return
        old = self.getDateTime()
        self._dateTime = QDateTime(dateTime)
        self._date = self._dateTime.date()
        self._updateText()
        self.dateTimeChanged.emit(self.getDateTime())
        if old.date() != dateTime.date():
            self.dateChanged.emit(self.getDate())
        if old.time() != dateTime.time():
            self.timeChanged.emit(self.getTime())

    def getDate(self):
        return QDate(self._dateTime.date())

    def setDate(self, date):
        if not isinstance(date, QDate):
            raise TypeError('date must be a QDate')
        if not date.isValid():
            self.reset()
            return
        value = self.getDateTime() if self._dateTime.isValid() else QDateTime(date, QTime(0, 0))
        value.setDate(date)
        self.setDateTime(value)

    def getTime(self):
        return QTime(self._dateTime.time())

    def setTime(self, time):
        if not isinstance(time, QTime):
            raise TypeError('time must be a QTime')
        if not time.isValid():
            self.reset()
            return
        value = self.getDateTime() if self._dateTime.isValid() else QDateTime(QDate.currentDate(), time)
        value.setTime(time)
        self.setDateTime(value)

    def getDateTimeFormat(self):
        return self._dateTimeFormat

    def setDateTimeFormat(self, format):
        self._dateTimeFormat = format
        self._dateFormat = format
        self._updateText()

    def setDateFormat(self, format):
        self.setDateTimeFormat(format)

    def isSecondVisible(self):
        return self._showSeconds

    def setSecondVisible(self, visible):
        self._showSeconds = bool(visible)
        if self._dateTimeFormat in ('yyyy-MM-dd HH:mm:ss', 'yyyy-MM-dd HH:mm'):
            self.setDateTimeFormat('yyyy-MM-dd HH:mm:ss' if visible else 'yyyy-MM-dd HH:mm')

    def setFlyoutAnimationType(self, aniType):
        self.flyoutAnimationType = aniType

    def reset(self):
        self.setDateTime(QDateTime())

    def _updateText(self):
        valid = self._dateTime.isValid()
        self.setText(self._dateTime.toString(self._dateTimeFormat) if valid
                     else self.tr('Pick a date and time'))
        self.setProperty('hasDate', valid)
        self.setStyle(QApplication.style())
        self.updateGeometry()
        self.update()

    def _showCalendarView(self):
        initial = self.getDateTime() if self._dateTime.isValid() else QDateTime.currentDateTime()
        view = _CalendarTimeView(initial, isinstance(self, FastCalendarPicker),
                                 self.isSecondVisible(), self.window())
        self._calendarTimeView = view
        view.calendarView.setResetEnabled(self.isRestEnabled())
        view.confirmed.connect(self.setDateTime)
        view.resetted.connect(self.reset)
        self._flyout = Flyout.make(view, self, self.window(), self.flyoutAnimationType)
        view.confirmed.connect(self._flyout.close)
        view.cancelled.connect(self._flyout.close)
        view.resetted.connect(self._flyout.close)

    def paintEvent(self, event):
        # CalendarPicker's button/QSS are unchanged; substitute the date-time icon.
        super(CalendarPicker, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self._dateTime.isValid():
            painter.setOpacity(0.6)
        if not self.isEnabled():
            painter.setOpacity(0.36)
        FluentIcon.DATE_TIME.render(painter, QRectF(self.width() - 23, self.height() / 2 - 6, 12, 12))

    dateTime = Property(QDateTime, getDateTime, setDateTime)
    date = Property(QDate, getDate, setDate)
    time = Property(QTime, getTime, setTime)
    dateTimeFormat = Property(object, getDateTimeFormat, setDateTimeFormat)
    dateFormat = Property(object, getDateTimeFormat, setDateFormat)
    secondVisible = Property(bool, isSecondVisible, setSecondVisible)


class CalendarTimePicker(_CalendarTimePickerMixin, CalendarPicker):
    """Date and 24-hour time selection using the original scrolling calendar."""


class FastCalendarTimePicker(_CalendarTimePickerMixin, FastCalendarPicker):
    """Date and time selection using the fast calendar's compact page model."""
