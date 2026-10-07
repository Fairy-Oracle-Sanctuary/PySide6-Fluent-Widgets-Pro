"""Register restored Pro components on the migrated gallery's category pages.

Factories remain lazy: pages contain native preview hosts, not a second
playground. CodeEdit/audio require an explicit click before optional imports.
"""
import importlib
import os
import sys
from functools import partial
from pathlib import Path

from PySide6.QtCore import QDate, QDateTime, QLibraryInfo, QObject, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QImage, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractButton, QButtonGroup, QGridLayout, QHBoxLayout, QTableWidgetItem,
    QVBoxLayout, QWidget,
)
import qfluentwidgets_pro as q

from ..common.config import cfg, REPO_URL


class LazySample(QWidget):
    """A preview built on first page visit; heavy demos need explicit opt-in."""

    def __init__(self, factory, owner, manual=False, height=0):
        super().__init__()
        self.factory = factory
        self.content = None
        self.owner = owner
        self.manual = manual
        self.previewHeight = height
        self.viewLayout = QVBoxLayout(self)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(280)
        self.loadButton = q.PushButton(owner.tr('Load demo'), self)
        self.loadButton.clicked.connect(self.materialize)
        self.viewLayout.addWidget(self.loadButton, 0, Qt.AlignLeft)
        self.errorLabel = q.BodyLabel(self)
        self.errorLabel.setWordWrap(True)
        self.errorLabel.hide()
        self.viewLayout.addWidget(self.errorLabel)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.manual:
            self.materialize()

    def materialize(self):
        if self.content is not None:
            return self.content
        try:
            content = self.factory()
        except ImportError as error:
            self.errorLabel.setText(self.owner.tr('Optional dependency unavailable: ') + str(error))
            self.errorLabel.show()
            return None
        self.content = content
        content.setParent(self)
        if self.previewHeight:
            content.setFixedHeight(self.previewHeight)
        # Let bounded previews fill their available width, then leave the
        # remaining space on the right rather than stretching the controls.
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(content, 1)
        row.addStretch(0)
        self.viewLayout.addLayout(row)
        self.loadButton.hide()
        self.errorLabel.hide()
        content.show()
        return content


class ProExamples(QObject):
    """One manifest drives coverage, placement, preview ownership and launchers."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.samples = {}
        self.windows = {}
        self._timers = []
        self._register()

    def add(self, category, names, factory, source, manual=False, height=0):
        names = names.split()
        page = getattr(self.window, category + 'Interface')
        host = LazySample(factory, self, manual, height)
        card = page.addExampleCard(' / '.join(names), host,
                                   REPO_URL + '/blob/main/qfluentwidgets_pro/' + source,
                                   stretch=1)
        # Component names must not impose a screen-wide minimum on the page.
        card.titleLabel.setWordWrap(True)
        card.titleLabel.setToolTip(' / '.join(names))
        for name in names:
            if name in self.samples:
                raise ValueError('Duplicate gallery component: ' + name)
            self.samples[name] = (page, card, host)

    def _register(self):
        add = self.add
        buttons = ('HyperlinkToolButton FilledPushButton FilledToolButton TextPushButton '
                   'TextToolButton OutlinedPushButton OutlinedToolButton '
                   'RoundPushButton RoundToolButton Chip Tag')
        add('basicInput', buttons, self._buttons, 'components/widgets/button.py')
        add('basicInput', 'LuminaPushButton', self._lumina, 'components/widgets/button.py')
        add('basicInput', 'IndeterminateProgressPushButton ProgressPushButton',
            self._progressButtons, 'components/widgets/button.py')
        add('basicInput', 'SubtitleCheckBox SubtitleRadioButton', self._subtitleInputs,
            'components/widgets/check_box.py')
        add('basicInput', 'ToolTipSlider RangeSlider', self._sliders,
            'components/widgets/slider.py')
        add('basicInput', 'MultiSelectionComboBox FontComboBox TreeComboBox MultiSelectionTreeComboBox',
            self._combos, 'components/widgets/tree_combo_box.py')
        add('basicInput', 'ExclusiveLiteFilter OutlinedExclusiveLiteFilter MultiSelectionLiteFilter '
            'OutlinedMultiSelectionLiteFilter', self._filters, 'components/widgets/exclusive_filter.py')
        add('basicInput', 'RatingWidget InteractiveRatingWidget', self._ratings,
            'components/widgets/rating_widget.py')
        add('basicInput', 'CircleColorPicker ScreenColorPicker DropDownColorPalette DropDownColorPicker',
            partial(self._demo, 'color_picker_demo', 'ColorPickerDemo'),
            'components/widgets/drop_down_color_picker.py', height=630)
        add('basicInput', 'ShortcutPicker',
            partial(self._demo, 'shortcut_picker_demo', 'ShortcutPickerDemo'),
            'components/widgets/shortcut_picker.py')
        add('dateTime', 'RangeCalendarPicker FastRangeCalendarPicker CalendarTimePicker FastCalendarTimePicker',
            self._calendars, 'components/date_time/range_calendar_picker.py')
        add('dialog', 'FlyoutDialog WaitingDialog Drawer', self._dialogs,
            'components/widgets/drawer.py')
        add('dialog', 'GuideWindow', partial(self._windowButton, 'GuideWindow'), 'window/guide_window.py')
        add('layout', 'Splitter', self._splitter, 'components/widgets/splitter.py', height=210)
        add('layout', 'WaterfallLayout', self._waterfall, 'components/layout/waterfall_layout.py', height=440)
        add('layout', 'DashboardCardWidget',
            partial(self._demo, 'dashboard_card_demo', 'DashboardCardDemo'),
            'components/widgets/dashboard_card.py', height=630)
        add('layout', 'ToolBox', partial(self._demo, 'tool_box_demo', 'ToolBoxDemo'),
            'components/widgets/tool_box.py', height=580)
        add('navigationView', 'Pager TopNavigationBar', self._navigation,
            'components/navigation/top_navigation_interface.py')
        add('navigationView', 'RoundTabBar',
            partial(self._demo, 'round_tab_bar_demo', 'RoundTabBarDemo'),
            'components/widgets/round_tab_bar.py')
        add('navigationView', 'RoundTabWidget',
            partial(self._demo, 'round_tab_widget_demo', 'RoundTabWidgetDemo'),
            'components/widgets/round_tab_widget.py')
        add('menu', 'MenuBar', partial(self._demo, 'menu_bar_demo', 'MenuBarDemo'),
            'components/widgets/menu_bar.py')
        add('navigationView', 'TopFluentWindow', partial(self._windowButton, 'TopFluentWindow'),
            'window/fluent_window.py')
        add('navigationView', 'FilledFluentWindow', partial(self._windowButton, 'FilledFluentWindow'),
            'window/filled_fluent_window.py')
        add('statusInfo', 'FilledProgressBar MultiSegmentProgressRing RadialGauge StepProgressBar',
            self._progress, 'components/widgets/progress_ring.py')
        add('statusInfo', 'Toast ProgressInfoBar ProgressToast RoundProgressToast',
            self._notifications, 'components/widgets/progress_toast.py')
        add('statusInfo', 'TimeLineWidget', self._timeline, 'components/widgets/time_line.py')
        add('statusInfo', 'ArticleSkeleton CirclePersonalInfoSkeleton RectanglePersonalInfoSkeleton SkeletonWidget',
            partial(self._demo, 'skeleton_demo', 'SkeletonDemo'),
            'components/widgets/skeleton.py', height=680)
        add('text', 'PinBox LabelLineEdit', self._text, 'components/widgets/line_edit.py')
        add('text', 'CodeEdit', partial(self._demo, 'code_edit_demo', 'CodeEditDemo'),
            'components/widgets/code_edit.py', manual=True, height=550)
        add('text', 'Watermark', partial(self._demo, 'watermark_demo', 'WatermarkDemo'),
            'components/widgets/watermark.py', height=650)
        add('view', 'RoundTableWidget LineTableWidget RoundTableView LineTableView',
            self._tables, 'components/widgets/table_view.py')
        add('view', 'RoundListWidget RoundListView TransparentRoundListWidget TransparentRoundListView '
            'CategoryCardListWidget CategoryCardListView', self._lists, 'components/widgets/list_view.py')
        add('view', 'DropSingleFileWidget DropMultiFilesWidget DropSingleFolderWidget DropMultiFoldersWidget DropAnyWidget',
            self._drop, 'components/widgets/drop_widget.py')
        add('view', 'ImageMagnifierWidget ImageComparisonSlider AvatarPicker ImageCropper',
            self._images, 'components/widgets/image_cropper.py')
        add('view', 'AudioWaveformWidget', self._audio, 'components/widgets/audio_waveform.py',
            manual=True, height=530)
        # The two larger demos continue to use the existing sidebar windows.
        add('view', 'ChartWidget', lambda: self._button(self.tr('Open charts'), self.window._openChartWindow),
            'components/widgets/chart_widget.py')
        add('view', 'ChatWidget', lambda: self._button(self.tr('Open chat'), self.window._openChatWindow),
            'components/widgets/chat_widget.py')

    def _demo(self, module, name):
        return getattr(importlib.import_module('gallery.pro_demos.' + module), name)()

    def _button(self, text, callback):
        button = q.PushButton(text)
        button.setMaximumWidth(button.sizeHint().width())
        button.clicked.connect(lambda checked=False: callback())
        return button

    def _column(self, *widgets, width=0, compact=False):
        host = QWidget()
        if width:
            host.setMaximumWidth(width)
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        for widget in widgets:
            if compact or isinstance(widget, QAbstractButton):
                layout.addWidget(widget, 0, Qt.AlignLeft)
            else:
                row = QHBoxLayout()
                row.setSpacing(0)
                row.addWidget(widget, 1)
                row.addStretch(0)
                layout.addLayout(row)
        return host

    def _buttons(self):
        host = QWidget()
        layout = q.FlowLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)
        widgets = [q.HyperlinkToolButton(q.FluentIcon.LINK, REPO_URL)]
        for cls in (q.FilledPushButton, q.TextPushButton,
                    q.OutlinedPushButton, q.RoundPushButton, q.Chip, q.Tag):
            widgets.append(cls(cls.__name__))
        for cls in (q.FilledToolButton, q.TextToolButton, q.OutlinedToolButton, q.RoundToolButton):
            widgets.append(cls(q.FluentIcon.ADD))
        for widget in widgets:
            layout.addWidget(widget)
        return host

    def _lumina(self):
        host = QWidget()
        layout = QVBoxLayout(host)
        # Graphics effects paint outside the button but cannot escape a clipped
        # preview ancestor. Reserve the whole hover glow on all four sides.
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(q.LuminaPushButton('LuminaPushButton'), 0, Qt.AlignLeft)
        return host

    def _progressButtons(self):
        indeterminate = q.IndeterminateProgressPushButton(self.tr('Download'))
        progress = q.ProgressPushButton(self.tr('Download'))
        for button in (indeterminate, progress):
            button.setFixedWidth(180)
        progress.setAutoProgressEnabled(True)
        timer = QTimer(progress)
        timer.setInterval(50)
        def tick():
            progress.setValue(progress.value() + 1)
            if progress.value() == 100:
                progress.setProgressing(False)
        def change(active):
            if active:
                progress.setValue(0)
                timer.start()
            else:
                timer.stop()
        timer.timeout.connect(tick)
        progress.progressChanged.connect(change)
        progress.stopRequested.connect(lambda: progress.setProgressing(False))
        self._timers.append(timer)
        return self._column(indeterminate, progress)

    def _subtitleInputs(self):
        check = q.SubtitleCheckBox(self.tr('Enable notifications'),
                                  self.tr('Receive updates when a task finishes.'))
        host = self._column(check, width=480)
        group = QButtonGroup(host)
        for text in ('Automatic', 'Manual'):
            radio = q.SubtitleRadioButton(self.tr(text), self.tr('Choose an operating mode.'))
            group.addButton(radio)
            host.layout().addWidget(radio, 0, Qt.AlignLeft)
        group.buttons()[0].setChecked(True)
        return host

    def _sliders(self):
        slider = q.ToolTipSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(45)
        span = q.RangeSlider(Qt.Horizontal)
        span.setRange(0, 100)
        span.setValues(20, 80)
        label = q.BodyLabel('20 — 80')
        span.rangeChanged.connect(lambda low, high: label.setText(f'{low} — {high}'))
        return self._column(slider, span, label, width=320)

    def _combos(self):
        multi = q.MultiSelectionComboBox()
        multi.addItems(['Python', 'C++', 'Rust', 'JavaScript'])
        multi.setChipsMode()
        multi.setSelectedIndices({0, 2})
        font = q.FontComboBox()
        font.setCurrentFont(q.getFont())
        single = q.TreeComboBox()
        multiple = q.MultiSelectionTreeComboBox()
        for combo in (single, multiple):
            leaves = []
            for name in ('Frontend', 'Backend'):
                parent = combo.addItem(name)
                leaves.extend(combo.addItems(['Python', 'TypeScript', 'Go'], parent))
            if combo is single:
                combo.setCurrentModelIndex(leaves[0])
            else:
                combo.setSelectedIndexes(leaves[:2])
        return self._column(multi, font, single, multiple, width=320)

    def _filters(self):
        widgets = []
        for cls in (q.ExclusiveLiteFilter, q.OutlinedExclusiveLiteFilter,
                    q.MultiSelectionLiteFilter, q.OutlinedMultiSelectionLiteFilter):
            widget = cls()
            widget.addItems(['All', 'Active', 'Completed', 'Pending'])
            widgets.append(widget)
        return self._column(*widgets, width=400)

    def _ratings(self):
        fixed = q.RatingWidget(4.5)
        value = q.DoubleSpinBox()
        value.setRange(0, 5)
        value.setSingleStep(.5)
        value.setValue(4.5)
        value.setFixedWidth(140)
        value.valueChanged.connect(fixed.setValue)
        active = q.InteractiveRatingWidget(3)
        label = q.BodyLabel('3')
        active.valueChanged.connect(lambda n: label.setText(str(n)))
        return self._column(fixed, value, active, label, compact=True)

    def _calendars(self):
        widgets = []
        for cls in (q.RangeCalendarPicker, q.FastRangeCalendarPicker):
            picker = cls()
            picker.setDateRange(QDate.currentDate(), QDate.currentDate().addDays(7))
            widgets.append(picker)
        for cls in (q.CalendarTimePicker, q.FastCalendarTimePicker):
            picker = cls()
            picker.setDateTime(QDateTime.currentDateTime())
            widgets.append(picker)
        return self._column(*widgets, width=320)

    def _dialogs(self):
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        flyout = self._button(self.tr('Show flyout dialog'), lambda: self._showFlyout(flyout))
        wait = self._button(self.tr('Show waiting dialog (Esc to close)'), self._showWaiting)
        layout.addWidget(flyout, 0, Qt.AlignLeft)
        layout.addWidget(wait, 0, Qt.AlignLeft)
        sides = QHBoxLayout()
        for text, side in (('Left', q.DrawerPosition.LEFT), ('Right', q.DrawerPosition.RIGHT),
                           ('Top', q.DrawerPosition.TOP), ('Bottom', q.DrawerPosition.BOTTOM)):
            sides.addWidget(self._button(self.tr(text), partial(self._showDrawer, side)))
        sides.addStretch(1)
        layout.addLayout(sides)
        return host

    def _showFlyout(self, button):
        dialog = q.FlyoutDialog(self.tr('Title'), self.tr('Custom dialog content.'))
        dialog.showAt(button, self.window)
        self._flyout = dialog

    def _showWaiting(self):
        if getattr(self, '_waiting', None) is not None:
            self._waiting.raise_()
            return
        dialog = q.WaitingDialog(self.tr('Please wait...'), self.tr('Preparing download...'), self.window)
        self._waiting = dialog
        dialog.finished.connect(lambda: setattr(self, '_waiting', None))
        dialog.finished.connect(dialog.deleteLater)
        dialog.open()

    def _showDrawer(self, side):
        if not hasattr(self, '_drawer'):
            self._drawer = q.Drawer(self.tr('Notifications'), self.window.stackedWidget)
            self._drawer.viewLayout.addStretch()
            self._drawer.addWidget(q.BodyLabel(self.tr('No more notifications')), alignment=Qt.AlignCenter)
            self._drawer.viewLayout.addStretch()
        self._drawer.open(side)

    def _windowButton(self, name):
        return self._button(self.tr('Open window') + ' — ' + name, partial(self.openWindow, name))

    def openWindow(self, name):
        if name not in self.windows:
            if name == 'GuideWindow':
                self.windows[name] = self._demo('guide_window_demo', 'GuideWindowDemo')
            elif name == 'FilledFluentWindow':
                self.windows[name] = self._demo('filled_window_demo', 'FilledWindowDemo')
            else:
                window = q.TopFluentWindow()
                window.setWindowTitle('TopFluentWindow')
                window.resize(960, 700)
                for key, icon in (('Home', q.FluentIcon.HOME), ('Settings', q.FluentIcon.SETTING)):
                    page = self._column(q.BodyLabel(key))
                    page.setObjectName('top' + key)
                    window.addSubInterface(page, icon, key)
                self.windows[name] = window
            self.windows[name].setWindowIcon(QIcon(':/gallery/images/logo.png'))
            self.windows[name].setMicaEffectEnabled(cfg.get(cfg.micaEnabled))
        window = self.windows[name]
        window.show()
        window.raise_()
        window.activateWindow()
        return window

    def _splitter(self):
        splitter = q.Splitter(Qt.Horizontal)
        for text in ('Left', 'Right'):
            splitter.addWidget(self._column(q.BodyLabel(self.tr(text)), q.LineEdit()))
        return splitter

    def _waterfall(self):
        host = QWidget()
        layout = q.WaterfallLayout(host)
        layout.setColumnWidth(160)
        for i, height in enumerate((100, 150, 80, 120, 110, 90, 140, 100)):
            card = q.CardWidget()
            card.setFixedHeight(height)
            content = QVBoxLayout(card)
            content.addWidget(q.BodyLabel(str(i + 1), card))
            layout.addWidget(card)
        return host

    def _navigation(self):
        pager = q.Pager(12, 5)
        nav = q.TopNavigationBar()
        result = q.BodyLabel('Home')
        for key, icon in (('Home', q.FluentIcon.HOME), ('Search', q.FluentIcon.SEARCH),
                           ('Settings', q.FluentIcon.SETTING)):
            nav.addItem(key, icon, key, onClick=partial(result.setText, key))
        nav.setCurrentItem('Home')
        return self._column(pager, nav, result, width=600)

    def _progress(self):
        bar = q.FilledProgressBar()
        bar.setValue(65)
        ring = q.MultiSegmentProgressRing()
        ring.setFixedSize(96, 96)
        ring.setSegments([(.45, QColor('#0078d4')), (.3, QColor('#16c79a')), (.25, QColor('#ffc857'))])
        gauge = q.RadialGauge()
        gauge.setFixedSize(96, 96)
        gauge.setValue(65)
        steps = q.StepProgressBar(4)
        steps.setStepNames(['Start', 'Upload', 'Process', 'Finish'])
        controls = q.Slider(Qt.Horizontal)
        bar.setMaximumWidth(320)
        controls.setMaximumWidth(320)
        controls.setRange(0, 100)
        controls.setValue(65)
        controls.valueChanged.connect(bar.setValue)
        controls.valueChanged.connect(gauge.setValue)
        return self._column(bar, ring, gauge, steps, controls, width=520)

    def _notifications(self):
        return self._column(
            self._button('Toast', lambda: q.Toast.success(self.tr('Completed'), self.tr('Task finished.'), parent=self.window)),
            self._button('ProgressInfoBar', lambda: self._notification(q.ProgressInfoBar)),
            self._button('ProgressToast', lambda: self._notification(q.ProgressToast)),
            self._button('RoundProgressToast', lambda: q.RoundProgressToast.new(duration=2500, parent=self.window)))

    def _notification(self, cls):
        if cls is q.ProgressInfoBar:
            toast = cls.new(self.tr('Download'), self.tr('Preparing download...'), parent=self.window)
        else:
            toast = cls.warning(self.tr('Preparing download...'), parent=self.window)
        timer = QTimer(toast)
        timer.setInterval(100)
        def tick():
            toast.setValue(toast.value() + 5)
            if toast.value() == 100:
                timer.stop()
        timer.timeout.connect(tick)
        timer.start()

    def _timeline(self):
        timeline = q.TimeLineWidget()
        timeline.setMaximumWidth(520)
        for title, icon, texts in (
            ('Completed', q.InfoBarIcon.SUCCESS, ('<s>Design approved</s>',)),
            ('Today', q.InfoBarIcon.INFORMATION, ('Build gallery', 'Run tests')),
            ('Pending', q.InfoBarIcon.ERROR, ('Publish release',))):
            group = timeline.addGroup(self.tr(title), icon)
            for text in texts:
                group.addItem(text, icon)
        return timeline

    def _text(self):
        edit = q.LabelLineEdit('https://', '.example')
        edit.setPlaceholderText(self.tr('Enter a name'))
        pin = q.PinBox()
        pin.setMaximumWidth(pin.sizeHint().width())
        return self._column(pin, edit, width=320)

    def _tables(self):
        host = QWidget()
        layout = QGridLayout(host)
        for i, cls in enumerate((q.RoundTableWidget, q.LineTableWidget, q.RoundTableView, q.LineTableView)):
            table = cls()
            table.setFixedHeight(190)
            if isinstance(table, (q.RoundTableWidget, q.LineTableWidget)):
                table.setRowCount(4)
                table.setColumnCount(2)
                table.setHorizontalHeaderLabels(['Name', 'Value'])
                for row in range(4):
                    for col in range(2):
                        table.setItem(row, col, QTableWidgetItem(str(row + col)))
            else:
                model = QStandardItemModel(table)
                model.setHorizontalHeaderLabels(['Name', 'Value'])
                for row in range(4):
                    model.appendRow([QStandardItem('Item ' + str(row)), QStandardItem(str(row))])
                table.setModel(model)
            layout.addWidget(self._column(q.BodyLabel(cls.__name__), table), i // 2, i % 2)
        return host

    def _lists(self):
        host = QWidget()
        layout = QGridLayout(host)
        for i, cls in enumerate((q.RoundListWidget, q.RoundListView, q.TransparentRoundListWidget,
                                 q.TransparentRoundListView, q.CategoryCardListWidget, q.CategoryCardListView)):
            view = cls()
            view.setFixedHeight(170)
            if hasattr(view, 'addItems'):
                view.addItems(['Python', 'C++', 'Rust'])
            else:
                model = QStandardItemModel(view)
                for text in ('Python', 'C++', 'Rust'):
                    model.appendRow(QStandardItem(text))
                view.setModel(model)
            layout.addWidget(self._column(q.BodyLabel(cls.__name__), view), i // 2, i % 2)
        return host

    def _drop(self):
        host = QWidget()
        layout = QGridLayout(host)
        for i, cls in enumerate((q.DropSingleFileWidget, q.DropMultiFilesWidget,
                                 q.DropSingleFolderWidget, q.DropMultiFoldersWidget, q.DropAnyWidget)):
            widget = cls()
            widget.setFixedHeight(125)
            layout.addWidget(self._column(q.BodyLabel(cls.__name__), widget), i // 2, i % 2)
        return host

    def _images(self):
        source = QImage(':/gallery/images/Shoko1.jpg')
        image = q.ImageMagnifierWidget(source)
        image.scaledToWidth(430)
        comparison = q.ImageComparisonSlider(source, QImage(':/gallery/images/Shoko2.jpg'))
        comparison.scaledToWidth(430)
        avatar = q.AvatarPicker(source)
        avatar.setRadius(40)
        preview = q.ImageLabel(source)
        preview.scaledToWidth(240)
        button = self._button(self.tr('Crop image'), partial(self._crop, source, preview))
        return self._column(image, comparison, avatar, preview, button, compact=True)

    def _crop(self, source, preview):
        editor = q.ImageCropper(source, self.window)
        editor.imageCropped.connect(lambda image: (preview.setImage(image), preview.scaledToWidth(240)))
        editor.exec()
        editor.deleteLater()

    def _audio(self):
        if sys.platform == 'win32':
            plugin = Path(QLibraryInfo.path(QLibraryInfo.PluginsPath)) / 'multimedia/windowsmediaplugin.dll'
            if plugin.is_file():
                os.environ.setdefault('QT_MEDIA_BACKEND', 'windows')
        return self._demo('audio_waveform_demo', 'AudioWaveformDemo')

    def closeWindows(self):
        for timer in self._timers:
            timer.stop()
        for window in self.windows.values():
            window.close()
