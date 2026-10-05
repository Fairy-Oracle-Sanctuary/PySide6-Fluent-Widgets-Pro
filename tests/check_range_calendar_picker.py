"""Range calendar API, real two-click selection, navigation and range painting."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Keep synthetic popup tests isolated from real desktop mouse/focus changes.
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QDate, QEvent, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QImage, QMouseEvent, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem, QWidget
from qfluentwidgets_pro import RangeCalendarPicker, FastRangeCalendarPicker, Theme, setTheme
from qfluentwidgets_pro.components.date_time import CalendarPicker, FastCalendarPicker
from shiboken6 import isValid


def index_for(view, date):
    scroll = view.dayView.scrollView
    if isinstance(view, QWidget) and scroll.count() > 42:
        index = scroll.model().index(scroll._dateToRow(date), 0)
        assert index.data(Qt.UserRole) == date
        return index
    for row in range(scroll.count()):
        index = scroll.model().index(row, 0)
        if index.data(Qt.UserRole) == date:
            return index
    raise AssertionError(f'Date not on page: {date.toString(Qt.ISODate)}')


def click_date(view, date):
    scroll = view.dayView.scrollView
    index = index_for(view, date)
    rect = scroll.visualRect(index)
    assert scroll.viewport().rect().contains(rect.center())
    QTest.mouseClick(scroll.viewport(), Qt.LeftButton, pos=rect.center())
    QTest.qWait(30)


def closed(popup):
    return not isValid(popup) or not popup.isVisible()


def run():
    app = QApplication([])
    owner = QWidget()
    owner.resize(700, 700)
    owner.show()
    start, end = QDate(2024, 3, 13), QDate(2024, 3, 21)
    for theme in (Theme.LIGHT, Theme.DARK):
        setTheme(theme)
        for cls in (RangeCalendarPicker, FastRangeCalendarPicker):
            picker = cls(owner)
            assert isinstance(picker, CalendarPicker)
            if cls is FastRangeCalendarPicker:
                assert isinstance(picker, FastCalendarPicker)
            picker.move(200, 500)
            picker.show()
            results = []
            picker.rangeChanged.connect(lambda a, b: results.append((a, b)))
            picker.setDateRange(end, start)
            assert picker.dateRange() == (start, end)
            assert picker.startDate == start and picker.endDate == end
            assert picker.text() == '2024-03-13 - 2024-03-21'
            picker.setDateRange(start, end)
            assert len(results) == 1
            picker.setDateFormat('yyyy/MM/dd')
            assert picker.text() == '2024/03/13 - 2024/03/21'
            picker.dateFormat = Qt.ISODate
            assert picker.text() == '2024-03-13 - 2024-03-21'
            picker.resize(picker.sizeHint())
            picker.setResetEnabled(True)
            picker._showCalendarView()
            view = picker._calendarView
            popup = picker._flyout if cls is FastRangeCalendarPicker else view
            QTest.qWait(350)
            assert popup.isVisible()
            assert view.rangeDelegate.start == start and view.rangeDelegate.end == end
            # Range band connects horizontally, with the same 3px vertical inset as circles.
            colors = []
            for date in (start.addDays(-1), start.addDays(1)):
                image = QImage(44, 44, QImage.Format_ARGB32_Premultiplied)
                image.fill(Qt.transparent)
                painter = QPainter(image)
                option = QStyleOptionViewItem()
                option.rect = QRect(0, 0, 44, 44)
                view.rangeDelegate._drawBackground(painter, option, index_for(view, date))
                painter.end()
                colors.append(image.pixelColor(0, 22).alpha())
                assert image.pixelColor(0, 1).alpha() == 0
                assert image.pixelColor(0, 42).alpha() == 0
            assert colors == [0, 28 if theme == Theme.DARK else 12]
            # The first click and hover must not mutate the committed value.
            click_date(view, end)
            assert popup.isVisible() and len(results) == 1
            scroll = view.dayView.scrollView
            pos = scroll.visualRect(index_for(view, start)).center()
            move = QMouseEvent(QEvent.MouseMove, QPointF(pos),
                               QPointF(scroll.viewport().mapToGlobal(pos)),
                               Qt.NoButton, Qt.NoButton, Qt.NoModifier)
            QApplication.sendEvent(scroll.viewport(), move)
            QTest.qWait(20)
            assert view.rangeDelegate.start == start and view.rangeDelegate.end == end, (
                cls.__name__, view._anchor, view.rangeDelegate.start, view.rangeDelegate.end)
            click_date(view, start)
            assert closed(popup) and picker.dateRange() == (start, end)
            QTest.qWait(30)
            picker._showCalendarView()
            view = picker._calendarView
            popup = picker._flyout if cls is FastRangeCalendarPicker else view
            QTest.qWait(350)
            click_date(view, start)
            click_date(view, start)
            assert picker.dateRange() == (start, start) and closed(popup)
            QTest.qWait(30)
            # Pick across months, retaining the anchor while navigating.
            picker._showCalendarView()
            view = picker._calendarView
            popup = picker._flyout if cls is FastRangeCalendarPicker else view
            QTest.qWait(350)
            click_date(view, QDate(2024, 3, 29))
            view.dayView.downButton.click()
            QTest.qWait(350)
            click_date(view, QDate(2024, 4, 3))
            assert picker.dateRange() == (QDate(2024, 3, 29), QDate(2024, 4, 3))
            QTest.qWait(30)
            picker.setDateRange(QDate(2024, 12, 29), QDate(2025, 1, 3))
            picker._showCalendarView()
            view = picker._calendarView
            popup = picker._flyout if cls is FastRangeCalendarPicker else view
            QTest.qWait(350)
            click_date(view, QDate(2024, 12, 31))
            view.dayView.downButton.click()
            QTest.qWait(350)
            click_date(view, QDate(2025, 1, 2))
            assert picker.dateRange() == (QDate(2024, 12, 31), QDate(2025, 1, 2))
            QTest.qWait(30)
            # Dismissing an incomplete range preserves the committed pair.
            picker.setDateRange(start, end)
            before = picker.dateRange()
            picker._showCalendarView()
            view = picker._calendarView
            popup = picker._flyout if cls is FastRangeCalendarPicker else view
            QTest.qWait(350)
            click_date(view, QDate(2024, 3, 27))
            QTest.keyClick(popup, Qt.Key_Escape)
            QTest.qWait(30)
            assert closed(popup) and picker.dateRange() == before
            picker._showCalendarView()
            view = picker._calendarView
            popup = picker._flyout if cls is FastRangeCalendarPicker else view
            QTest.qWait(350)
            click_date(view, QDate(2024, 3, 27))
            QTest.mouseClick(owner, Qt.LeftButton, pos=QPoint(650, 650))
            QTest.qWait(30)
            assert closed(popup) and picker.dateRange() == before
            # Reset and invalid input validation.
            picker._showCalendarView()
            view = picker._calendarView
            popup = picker._flyout if cls is FastRangeCalendarPicker else view
            QTest.qWait(350)
            view.dayView.resetButton.click()
            QTest.qWait(30)
            assert closed(popup)
            assert not picker.startDate.isValid() and not picker.property('hasDate')
            assert not results[-1][0].isValid()
            try:
                picker.setDateRange(start, QDate())
            except ValueError:
                pass
            else:
                raise AssertionError('Invalid half-range accepted')
            picker.date = start
            assert picker.dateRange() == (start, start)
            picker.setDisabledWeekDays({Qt.Saturday, Qt.Sunday})
            assert picker.disabledWeekDays() == {6, 7}
            try:
                picker.setDateRange(QDate(2024, 3, 16), end)
            except ValueError:
                pass
            else:
                raise AssertionError('Disabled weekend endpoint accepted')
            picker._showCalendarView()
            view = picker._calendarView
            popup = picker._flyout if cls is FastRangeCalendarPicker else view
            QTest.qWait(350)
            click_date(view, QDate(2024, 3, 16))
            assert not view._anchor.isValid() and popup.isVisible()
            click_date(view, QDate(2024, 3, 15))
            click_date(view, QDate(2024, 3, 16))
            assert view._anchor == QDate(2024, 3, 15) and popup.isVisible()
            click_date(view, QDate(2024, 3, 18))
            assert picker.dateRange() == (QDate(2024, 3, 15), QDate(2024, 3, 18))
            assert closed(popup)
            QTest.qWait(30)
            picker.setDisabledWeekDays({5})
            assert not picker.startDate.isValid()
            picker.deleteLater()
            app.processEvents()
    owner.close()
    print('PASS: both range calendars, themes, signals, preview, reverse/same-day/cross-month/year selection, outside click, Esc and reset')


if __name__ == '__main__':
    run()
