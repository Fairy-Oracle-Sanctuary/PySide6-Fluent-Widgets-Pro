"""Combined calendar/time APIs, transactional popup and reused wheel interaction."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QDate, QDateTime, QPoint, QTime, QTimeZone, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from shiboken6 import isValid

from qfluentwidgets_pro import (
    CalendarTimePicker, FastCalendarTimePicker, Theme, setTheme,
)
from qfluentwidgets_pro.components.date_time.calendar_view import CalendarView
from qfluentwidgets_pro.components.date_time.fast_calendar_view import FastCalendarView


def click_date(view, date):
    scroll = view.calendarView.dayView.scrollView
    for row in range(scroll.count()):
        index = scroll.model().index(row, 0)
        if index.data(Qt.UserRole) == date:
            rect = scroll.visualRect(index)
            assert scroll.viewport().rect().contains(rect.center())
            QTest.mouseClick(scroll.viewport(), Qt.LeftButton, pos=rect.center())
            QTest.qWait(30)
            return
    raise AssertionError(f'Date not on calendar: {date}')


def closed(popup):
    return not isValid(popup) or not popup.isVisible()


def open_view(picker):
    picker._showCalendarView()
    QTest.qWait(350)
    assert picker._flyout.isVisible()
    return picker._calendarTimeView, picker._flyout


def run():
    app = QApplication([])
    owner = QWidget()
    owner.resize(900, 750)
    owner.show()
    original = QDateTime(QDate(2026, 2, 10), QTime(20, 0, 0), QTimeZone(b'UTC'))
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        for cls in (CalendarTimePicker, FastCalendarTimePicker):
            picker = cls(owner)
            picker.move(300, 500)
            picker.show()
            dates, times, values = [], [], []
            picker.dateChanged.connect(dates.append)
            picker.timeChanged.connect(times.append)
            picker.dateTimeChanged.connect(values.append)
            assert not picker.dateTime.isValid()
            view, popup = open_view(picker)
            assert view.dateTime().isValid() and not picker.dateTime.isValid()
            view.cancelButton.click()
            QTest.qWait(30)
            assert closed(popup) and not values and not picker.dateTime.isValid()
            picker.setDateTime(original)
            assert picker.dateTime == original
            assert picker.text() == '2026-02-10 20:00:00'
            assert picker.property('hasDate')
            picker.setDateTime(original)
            assert (len(dates), len(times), len(values)) == (1, 1, 1)
            copy = picker.dateTime
            copy.setDate(QDate(2000, 1, 1))
            assert picker.date == original.date()
            picker.time = QTime(0, 0, 0)
            assert picker.time.isValid() and picker.time == QTime(0, 0, 0)
            assert picker.dateTime.isValid() and picker.dateTime.timeZone() == original.timeZone()
            assert len(dates) == 1 and len(times) == 2 and len(values) == 2
            picker.date = QDate(2026, 2, 11)
            assert picker.time == QTime(0, 0) and len(times) == 2
            picker.dateTimeFormat = 'yyyy/MM/dd HH:mm:ss'
            assert picker.text() == '2026/02/11 00:00:00'
            picker.setSecondVisible(False)
            assert picker.dateTimeFormat == 'yyyy/MM/dd HH:mm:ss'
            picker.setDateTimeFormat('yyyy-MM-dd HH:mm')
            picker.secondVisible = True
            assert picker.dateTimeFormat == 'yyyy-MM-dd HH:mm:ss'
            picker.setDateTime(original)
            picker.resize(picker.sizeHint())

            view, popup = open_view(picker)
            expected = FastCalendarView if cls is FastCalendarTimePicker else CalendarView
            assert isinstance(view.calendarView, expected)
            assert len(view.timePanel.listWidgets) == 3
            assert (view.width(), view.height()) == (601, 394)
            assert view.timePanel.value() == ['20', '0', '0']
            assert not view.yesButton.toolTip() and not view.cancelButton.toolTip()
            # Both date and wheels remain a draft until the shared confirm action.
            count = len(values)
            click_date(view, QDate(2026, 2, 12))
            assert popup.isVisible() and picker.dateTime == original and len(values) == count
            column = view.timePanel.column(0)
            rect = column.visualItemRect(column.item(column.currentIndex() + 1))
            QTest.mouseClick(column.viewport(), Qt.LeftButton, pos=rect.center())
            QTest.qWait(300)
            assert view.timePanel.value()[0] == '21'
            assert picker.dateTime == original
            # The mask overlays the actual selected row, not hard-coded popup offsets.
            mask = view.timePanel.itemMaskWidget
            for column in view.timePanel.listWidgets:
                row = column.visualItemRect(column.currentItem())
                center = mask.mapFromGlobal(column.viewport().mapToGlobal(row.center()))
                assert abs(center.y() - mask.rect().center().y()) <= 2, (column.currentItem().text(), row, center, mask.geometry(), column.vScrollBar.value())
            view.yesButton.click()
            QTest.qWait(30)
            assert closed(popup) and len(values) == count + 1
            assert picker.date == QDate(2026, 2, 12) and picker.time == QTime(21, 0)
            assert picker.dateTime.timeZone() == original.timeZone()

            # Midnight is valid, and cancelled drafts never leak to the button.
            for action in ('cancel', 'escape', 'outside'):
                view, popup = open_view(picker)
                before = picker.dateTime
                count = len(values)
                click_date(view, QDate(2026, 2, 13))
                view.timePanel.setValue(['0', '0', '0'])
                assert view.dateTime().time() == QTime(0, 0)
                if action == 'cancel':
                    view.cancelButton.click()
                elif action == 'escape':
                    QTest.keyClick(view, Qt.Key_Escape)
                else:
                    QTest.mouseClick(owner, Qt.LeftButton, pos=QPoint(880, 730))
                QTest.qWait(30)
                assert closed(popup) and picker.dateTime == before and len(values) == count

            view, popup = open_view(picker)
            view.timePanel.setValue(['0', '0', '0'])
            QTest.keyClick(view, Qt.Key_Return)
            QTest.qWait(30)
            assert closed(popup) and picker.time == QTime(0, 0)
            # Year/month navigation still uses the original calendar implementation.
            view, popup = open_view(picker)
            view.calendarView.dayView.downButton.click()
            QTest.qWait(350)
            click_date(view, QDate(2026, 3, 2))
            view.calendarView.dayView.titleButton.click()
            assert view.calendarView.stackedWidget.currentWidget() is view.calendarView.monthView
            view.calendarView.monthView.titleButton.click()
            assert view.calendarView.stackedWidget.currentWidget() is view.calendarView.yearView
            view.calendarView.yearView.itemClicked.emit(QDate(2026, 1, 1))
            assert view.calendarView.stackedWidget.currentWidget() is view.calendarView.monthView
            view.calendarView.monthView.itemClicked.emit(QDate(2026, 3, 1))
            assert view.calendarView.stackedWidget.currentWidget() is view.calendarView.dayView
            assert popup.isVisible() and view.timePanel.value() == ['0', '0', '0']
            view.yesButton.click()
            QTest.qWait(30)
            assert picker.date == QDate(2026, 3, 2)

            picker.setSecondVisible(False)
            picker.setTime(QTime(12, 34, 56))
            view, popup = open_view(picker)
            assert len(view.timePanel.listWidgets) == 2
            assert view.timePanel.value() == ['12', '34']
            view.yesButton.click()
            QTest.qWait(30)
            assert picker.time == QTime(12, 34, 0)
            picker.setResetEnabled(True)
            view, popup = open_view(picker)
            assert not view.calendarView.dayView.resetButton.isHidden()
            view.calendarView.dayView.resetButton.click()
            QTest.qWait(30)
            assert closed(popup) and not picker.dateTime.isValid()
            assert not picker.property('hasDate') and not values[-1].isValid()
            count = len(values)
            picker.reset()
            assert len(values) == count
            picker.setDate(QDate(2024, 2, 29))
            assert picker.dateTime.isValid() and picker.time == QTime(0, 0)
            picker.reset()
            picker.setTime(QTime(0, 0))
            assert picker.date == QDate.currentDate() and picker.dateTime.isValid()
            for setter in (picker.setDateTime, picker.setDate, picker.setTime):
                try:
                    setter('invalid')
                except TypeError:
                    pass
                else:
                    raise AssertionError('Invalid input type accepted')
            picker.setDateTime(original)
            offset = original.toTimeZone(QTimeZone(8 * 3600))
            picker.setDateTime(offset)  # same instant, different display/timezone
            assert picker.date == QDate(2026, 2, 11) and picker.time == QTime(4, 0)
            assert picker.dateTime.timeZone() == offset.timeZone()
            picker.deleteLater()
            app.processEvents()
    owner.close()
    print('PASS: both calendar/time pickers, themes, signals, UTC, midnight, real date/wheel clicks, confirm/cancel/outside/Esc, navigation, seconds and reset')


if __name__ == '__main__':
    run()
