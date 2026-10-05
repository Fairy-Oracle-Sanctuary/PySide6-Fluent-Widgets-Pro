"""Date-range pickers sharing the existing standard and fast calendars."""
from typing import Union

from PySide6.QtCore import QDate, QEvent, QPoint, Property, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPen
from PySide6.QtWidgets import QApplication, QStyle

from ...common.style_sheet import isDarkTheme, themeColor
from ..widgets.flyout import Flyout
from .calendar_picker import CalendarPicker, FastCalendarPicker
from .calendar_view import CalendarView, DayScrollItemDelegate
from .fast_calendar_view import FastCalendarView


def _ordered(start, end):
    return (QDate(start), QDate(end)) if start <= end else (QDate(end), QDate(start))


class _RangeDayDelegate(DayScrollItemDelegate):
    def __init__(self, original):
        super().__init__(original.min, original.max)
        self.start = QDate()
        self.end = QDate()
        self.disabledWeekDays = frozenset()

    def setSelectedDate(self, date):
        # FastDayScrollView's single-date compatibility hook; range painting
        # uses start/end instead, so the old selection ring is not drawn.
        self.selectedDate = QDate(date)

    def _drawBackground(self, painter, option, index):
        date = index.data(Qt.UserRole)
        if not isinstance(date, QDate) or not date.isValid():
            return
        painter.save()
        if self.start.isValid() and self.start <= date <= self.end:
            # Match the circles' height, while keeping adjacent cells connected.
            band = option.rect.adjusted(0, 3, 0, -3)
            if date == self.start:
                band.setLeft(option.rect.center().x())
            if date == self.end:
                band.setRight(option.rect.center().x())
            painter.fillRect(band, QColor(255, 255, 255, 28) if isDarkTheme()
                             else QColor(0, 0, 0, 12))
        endpoint = date in (self.start, self.end)
        painter.setPen(QPen(themeColor(), 1.4) if endpoint and date != QDate.currentDate()
                       else Qt.NoPen)
        if date == QDate.currentDate():
            painter.setBrush(themeColor())
        elif endpoint:
            painter.setBrush(QColor(61, 61, 61) if isDarkTheme() else QColor(243, 243, 243))
        elif option.state & QStyle.State_MouseOver:
            painter.setBrush(QColor(255, 255, 255, 9) if isDarkTheme()
                             else QColor(0, 0, 0, 9))
        else:
            painter.setBrush(Qt.transparent)
        painter.drawEllipse(option.rect.adjusted(3, 3, -3, -3))
        painter.restore()

    def _drawText(self, painter, option, index):
        date = index.data(Qt.UserRole)
        if not isinstance(date, QDate) or not date.isValid():
            return
        painter.save()
        disabled = date.dayOfWeek() in self.disabledWeekDays
        font = QFont(self.font)
        font.setStrikeOut(disabled and self.min <= date <= self.max)
        painter.setFont(font)
        if disabled:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            painter.setOpacity(0.4 if self.min <= date <= self.max else 0.6)
        elif date == QDate.currentDate():
            painter.setPen(Qt.black if isDarkTheme() else Qt.white)
        elif date in (self.start, self.end):
            painter.setPen(themeColor())
        else:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            if not self.min <= date <= self.max:
                painter.setOpacity(0.6)
        painter.drawText(option.rect, Qt.AlignCenter, index.data(Qt.DisplayRole))
        painter.restore()


class _RangeViewMixin:
    rangeChanged = Signal(QDate, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._start = QDate()
        self._end = QDate()
        self._anchor = QDate()
        scroll = self.dayView.scrollView
        self.rangeDelegate = _RangeDayDelegate(scroll.delegate)
        self.rangeDelegate.setParent(scroll)
        scroll.delegate = self.rangeDelegate
        scroll.setItemDelegate(self.rangeDelegate)
        scroll.setMouseTracking(True)
        scroll.viewport().setMouseTracking(True)
        scroll.viewport().installEventFilter(self)

    def setDisabledWeekDays(self, days):
        self.rangeDelegate.disabledWeekDays = frozenset(days)
        self.dayView.scrollView.viewport().update()

    def _isSelectable(self, date):
        return (isinstance(date, QDate) and date.isValid()
                and date.dayOfWeek() not in self.rangeDelegate.disabledWeekDays)

    def setDateRange(self, start, end):
        self._start, self._end = _ordered(start, end)
        self._anchor = QDate()
        self.dayView.setDate(self._start)
        self._highlight(self._start, self._end)

    def _highlight(self, start, end):
        self.rangeDelegate.start, self.rangeDelegate.end = _ordered(start, end)
        self.dayView.scrollView.viewport().update()

    def _onDayItemClicked(self, date):
        if not self._isSelectable(date):
            return
        if not self._anchor.isValid():
            self._anchor = QDate(date)
            self._highlight(date, date)
        else:
            self._start, self._end = _ordered(self._anchor, date)
            self._anchor = QDate()
            self._highlight(self._start, self._end)
            self.rangeChanged.emit(self._start, self._end)
            if isinstance(self, CalendarView):
                self.close()

    def eventFilter(self, watched, event):
        if self.isVisible():
            if event.type() == QEvent.MouseButtonPress:
                position = self.stackedWidget.mapFromGlobal(event.globalPosition().toPoint())
                if not self.stackedWidget.rect().contains(position):
                    self.window().close()
                    return True
            elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
                self.window().close()
                return True
        scroll = self.dayView.scrollView
        if watched is scroll.viewport() and self._anchor.isValid():
            if event.type() == QEvent.MouseMove:
                index = scroll.indexAt(event.position().toPoint())
                date = index.data(Qt.UserRole)
                if self._isSelectable(date):
                    self._highlight(self._anchor, date)
            elif event.type() == QEvent.Leave:
                self._highlight(self._anchor, self._anchor)
        return super().eventFilter(watched, event)

    def showEvent(self, event):
        QApplication.instance().installEventFilter(self)
        super().showEvent(event)

    def hideEvent(self, event):
        QApplication.instance().removeEventFilter(self)
        super().hideEvent(event)


class _RangeCalendarView(_RangeViewMixin, CalendarView):
    pass


class _FastRangeCalendarView(_RangeViewMixin, FastCalendarView):
    pass


class _RangePickerMixin:
    """Commit only complete ranges; reuse CalendarPicker styling and date format."""
    rangeChanged = Signal(QDate, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._startDate = QDate()
        self._endDate = QDate()
        self._calendarView = None
        self._flyout = None
        self._disabledWeekDays = frozenset()
        self.setText(self.tr('Pick a date range'))

    def getStartDate(self):
        return QDate(self._startDate)

    def getEndDate(self):
        return QDate(self._endDate)

    def dateRange(self):
        return self.getStartDate(), self.getEndDate()

    def disabledWeekDays(self):
        """Return disabled weekdays, numbered Monday=1 through Sunday=7."""
        return set(self._disabledWeekDays)

    def setDisabledWeekDays(self, days):
        """Disable range endpoints on these weekdays; interior dates stay included."""
        values = [getattr(day, 'value', day) for day in days]
        if any(type(day) is not int or not 1 <= day <= 7 for day in values):
            raise ValueError('Weekdays must be integers from 1 (Monday) to 7 (Sunday)')
        self._disabledWeekDays = frozenset(values)
        if (self._startDate.isValid() and
                (self._startDate.dayOfWeek() in values or self._endDate.dayOfWeek() in values)):
            self.reset()

    def setDateRange(self, start: QDate, end: QDate):
        """Set both endpoints, sorting reversed ranges; invalid pairs clear it."""
        if not isinstance(start, QDate) or not isinstance(end, QDate):
            raise TypeError('Range endpoints must be QDate values')
        if not start.isValid() and not end.isValid():
            self.reset()
            return
        if not start.isValid() or not end.isValid():
            raise ValueError('Both range endpoints must be valid')
        if start.dayOfWeek() in self._disabledWeekDays or end.dayOfWeek() in self._disabledWeekDays:
            raise ValueError('Range endpoints cannot fall on a disabled weekday')
        start, end = _ordered(start, end)
        if (start, end) == self.dateRange():
            return
        self._startDate, self._endDate = start, end
        self._date = QDate(start)
        self._updateRangeText()
        self.rangeChanged.emit(QDate(start), QDate(end))

    def setDate(self, date: QDate):
        """Compatibility with CalendarPicker: select a single-day range."""
        self.setDateRange(date, date)

    def setDateFormat(self, format: Union[Qt.DateFormat, str]):
        self._dateFormat = format
        self._updateRangeText()

    def reset(self):
        hadRange = self._startDate.isValid()
        self._startDate, self._endDate, self._date = QDate(), QDate(), QDate()
        self._updateRangeText()
        if hadRange:
            self.rangeChanged.emit(QDate(), QDate())

    def _updateRangeText(self):
        hasRange = self._startDate.isValid() and self._endDate.isValid()
        self.setText(f'{self._startDate.toString(self._dateFormat)} - '
                     f'{self._endDate.toString(self._dateFormat)}' if hasRange
                     else self.tr('Pick a date range'))
        self.setProperty('hasDate', hasRange)
        self.setStyle(QApplication.style())
        self.updateGeometry()
        self.update()

    def _showCalendarView(self):
        fast = isinstance(self, FastCalendarPicker)
        view = (_FastRangeCalendarView if fast else _RangeCalendarView)(self.window())
        self._calendarView = view
        view.setDisabledWeekDays(self._disabledWeekDays)
        view.setResetEnabled(self.isRestEnabled())
        view.rangeChanged.connect(self.setDateRange)
        view.resetted.connect(self.reset)
        if self._startDate.isValid():
            view.setDateRange(self._startDate, self._endDate)
        if fast:
            self._flyout = Flyout.make(view, self, self.window(), self.flyoutAnimationType)
            view.rangeChanged.connect(self._flyout.close)
            view.resetted.connect(self._flyout.close)
        else:
            x = int(self.width() / 2 - view.sizeHint().width() / 2)
            view.exec(self.mapToGlobal(QPoint(x, self.height())))

    startDate = Property(QDate, getStartDate)
    endDate = Property(QDate, getEndDate)
    date = Property(QDate, CalendarPicker.getDate, setDate)
    dateFormat = Property(object, CalendarPicker.getDateFormat, setDateFormat)


class RangeCalendarPicker(_RangePickerMixin, CalendarPicker):
    """Two-click date range using CalendarPicker's animated scrolling calendar."""


class FastRangeCalendarPicker(_RangePickerMixin, FastCalendarPicker):
    """Two-click date range using FastCalendarPicker's compact paged calendar."""
