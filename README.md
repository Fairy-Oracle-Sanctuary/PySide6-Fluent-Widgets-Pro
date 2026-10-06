<p align="center">
  <img width="18%" align="center" src="qfluentwidgets_pro\_rc\images\logo.png" alt="logo">
</p>
  <h1 align="center">
  PySide6-Fluent-Widgets-Pro
</h1>
<p align="center">
  A fluent design widgets library based on <a href="https://github.com/zhiyiYo/PyQt-Fluent-Widgets">PyQt-Fluent-Widgets</a>
</p>

<div align="center">

[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](https://github.com/Fairy-Oracle-Sanctuary/Qt-Fluent-Widgets)
[![GPLv3](https://img.shields.io/badge/License-GPLv3-blue?color=#4ec820)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?color=#4ec820)]()
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.qt.io)

</div>

<p align="center">
English | <a href="docs/README_zh.md">简体中文</a>
</p>

<p align="center">
  <img src="docs/source/_static/Interface.png" alt="interface"/>
</p>

## 📌 Introduction

This repository is based on the **free version** of QFluentWidgets (PySide6 port) and aims to **restore / re-implement some components and behaviors from the Pro version**.

Only a subset has been restored so far. The goal is to provide a drop-in, developer-friendly widget library for PySide6 with a Fluent Design look & feel.

## ✨ Status

- **[scope]** Partial restoration (work in progress)
- **[target]** Restore commonly used Pro widgets/components first
- **[compatibility]** Python 3.9+ / Windows, macOS, Linux

## 🧩 Restored Components

91 components have been restored or extended in this repo (the list will be updated continuously):

`HyperlinkToolButton` `FilledPushButton` `FilledToolButton`
`TextPushButton` `TextToolButton` `LuminaPushButton`
`IndeterminateProgressPushButton`
`ProgressPushButton`
`TimeLineWidget`
`FlyoutDialog`
`RangeCalendarPicker` `FastRangeCalendarPicker`
`CalendarTimePicker` `FastCalendarTimePicker`
`AudioWaveformWidget`
`CircleColorPicker`
`ScreenColorPicker`
`DropDownColorPalette`
`DropDownColorPicker`
`ShortcutPicker`
`WaitingDialog`
`MenuBar`
`GuideWindow`
`RoundTabBar`
`RoundTabWidget`
`ChatWidget`
`SkeletonWidget` `ArticleSkeleton` `CirclePersonalInfoSkeleton` `RectanglePersonalInfoSkeleton`
`Watermark`
`Drawer`
`DashboardCardWidget`
`ToolBox`
`ImageMagnifierWidget`
`ImageComparisonSlider`
`ImageCropper`
`AvatarPicker`
`CodeEdit`
`ProgressInfoBar`
`ProgressToast`
`RoundProgressToast`
`RatingWidget`
`InteractiveRatingWidget`
`OutlinedPushButton` `OutlinedToolButton` `RoundPushButton`
`RoundToolButton` `Chip` `Tag` `SubtitleCheckBox`
`SubtitleRadioButton` `ToolTipSlider` `RangeSlider`
`Pager` `FilledProgressBar` `MultiSegmentProgressRing`
`RadialGauge` `DropMultiFilesWidget` `DropSingleFileWidget`
`TopFluentWindow` `ChartWidget` `Splitter` `PinBox`
`FilledFluentWindow`
`LabelLineEdit` `StepProgressBar` `RoundTableWidget`
`RoundTableView` `LineTableWidget` `LineTableView`
`DropSingleFolderWidget` `DropMultiFoldersWidget`
`MultiSelectionComboBox` `RoundListWidget` `RoundListView`
`TransparentRoundListWidget` `TransparentRoundListView`
`CategoryCardListWidget` `CategoryCardListView`
`Toast` `FontComboBox` `ExclusiveLiteFilter`
`OutlinedExclusiveLiteFilter` `MultiSelectionLiteFilter`
`OutlinedMultiSelectionLiteFilter` `WaterfallLayout`
`TopNavigationBar` `DropAnyWidget`
`TreeComboBox` `MultiSelectionTreeComboBox`

## 🚀 Installation

This repository is intended to be used as a source dependency.

### Option 1: Clone and run the demo

```bash
git clone https://github.com/<your-name>/PySide6-Fluent-Widgets-Extend.git
python main.py
```

### Option 2: Use in your own project

Copy the `qfluentwidgets_pro` folder into your project (or add this repo to your Python path), then:

```python
from qfluentwidgets_pro import FluentWidget
```

Dependencies:

- PySide6 (Qt for Python)

## 🧪 Quick Start

```python
from PySide6.QtWidgets import QApplication, QVBoxLayout
from qfluentwidgets_pro import (
    FluentWidget, FluentIcon, ToolTipSlider, RangeSlider,
    HyperlinkToolButton, IndeterminateProgressPushButton,
)


class Window(FluentWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(ToolTipSlider())

        rs = RangeSlider()
        rs.setRange(0, 100)
        rs.setValues(20, 80)
        layout.addWidget(rs)

        layout.addWidget(HyperlinkToolButton(FluentIcon.LINK, "https://github.com"))

        self.progressButton = IndeterminateProgressPushButton("Downloading...", self)
        layout.addWidget(self.progressButton)


app = QApplication([])
w = Window()
w.show()
app.exec()
```

`IndeterminateProgressPushButton` follows the current theme and accent color.
Its loading animation starts automatically; use `start()` and `stop()` to control
it, and `isSpinning()` to query its state. Clicking the button emits the usual
`clicked` signal without changing the animation state.

`ProgressPushButton` uses the primary button appearance when idle and a centered
progress ring with a stop icon while progressing. Use `setProgressing(True)` and
`setValue(0..100)` to control it. `setAutoProgressEnabled(True)` enables click-to-start
(off by default). Handle `stopRequested` to cancel; completion does not automatically
change the component state. The Buttons demo includes a simulated download.

`ImageComparisonSlider(before, after)` compares two images using a draggable vertical
divider and translucent arrow grip. Inputs accept paths, QImage or QPixmap.
Use `setImages()` to replace them and `setValue(0..100)` to set the split percentage;
`valueChanged` reports changes. Arrow keys and Home/End are supported.
The Magnifier page includes a two-image comparison example.

`Toast.success(title, content, parent=window)` displays a compact notification with
a green top accent, title/content and optional close button. `info`, `warning` and
`error` are also available; `duration=-1` keeps the notification until closed.
`ToastPosition` supports six placements, with independent stacks per parent window.
The Home page's Success button shows the Lesson 4 reference example.

`ProgressInfoBar` reuses InfoBar placement, stacking, neutral background and close
button, with the existing indeterminate ring animation. It stays open by default;
closing the notification does not cancel a task. The Home page includes an example.

```python
from qfluentwidgets_pro import ProgressInfoBar
bar = ProgressInfoBar.new("Please wait", "Sending email...", parent=window)
bar.setContent("Uploading attachments...")
bar.setRemainingTime("Remaining: 10 s")  # optional caller-formatted text
bar.setValue(65)                        # switches to determinate progress (0..100)
bar.setIndeterminate(True)              # resumes the indeterminate ring
bar.close()                            # close when the task finishes
```

`setTitle()` and `setCustomBarColor(light, dark)` are also available. An empty
remaining-time string removes the suffix. `InfoBarPosition` provides placement;
`duration=-1` keeps it open, and `closedSignal` / `valueChanged` report changes.

`ProgressToast` is a compact single-message task notification with a status icon,
close button, shadow and a bottom progress stripe. It shares Toast placement and
stacking. `info`, `warning`, `error` start at 0; `success` starts at 100. All stay
open by default. Progress does not automatically change status or close the toast.

```python
from qfluentwidgets_pro import ProgressToast, InfoBarIcon
toast = ProgressToast.warning("Downloading, please wait...", value=77, parent=window)
toast.setStateColor(InfoBarIcon.WARNING, "#9D5D00", "#FCE100")
toast.setStateColor(InfoBarIcon.SUCCESS, "#0F7B0F", "#6CCB5F")
toast.setValue(100)
toast.setIcon(InfoBarIcon.SUCCESS)
toast.setContent("File downloaded successfully")
```

State colors are customizable; the icon and stripe always share the selected
color. `setStateColor(status, light, dark=None)` sets individual state colors;
`setCustomBarColor(light, dark=None)` supplies a fallback for states without an
override. Omitting `dark` uses the same color in both themes. `setUseAni(False)`
disables value interpolation. `ToastPosition`, `duration`, `isClosable`, `closed`
and `valueChanged` are supported. Closing does not cancel a task. The Home page
includes a simulated download and the completed state.

`RoundProgressToast` is a capsule-shaped loading notification with an
`IndeterminateProgressRing` and message, without a close button or status stripe.
The ring follows the current accent color in both themes and pauses while hidden.
It shares Toast placement, stacking and the `closed` signal.

```python
from qfluentwidgets_pro import RoundProgressToast
toast = RoundProgressToast.new("Loading, please wait", parent=window)
toast.setContent("Processing...")
toast.close()  # call when the task ends
```

The default `duration=-1` keeps it open; a nonnegative duration dismisses it
automatically. The Home page demonstrates a five-second loading notification.

`RatingWidget(4.5)` displays a numeric score followed by an orange vector star.
Use `setValue(number)` to update it; `valueChanged(float)` reports changes.
It is a display widget, not a clickable five-star selector, and is not restricted
to a five-point scale. `setDecimals(0..6)` controls display precision (default 1,
with trailing zeros omitted); `setStarColor(light, dark=None)` customizes the star.
The Home page includes a score input for testing updates.

`InteractiveRatingWidget(3)` displays five orange stars. Hovering fills all
preceding stars and clips the current star at the exact pointer X coordinate,
without whole-star or half-star rounding. Click to confirm; leaving restores
the confirmed score. `setValue(0..5)` sets the score programmatically,
`hovered(float)` reports previews, and `valueChanged(float)` reports confirmed
changes. `displayValue()` returns the currently displayed score.
`setReadOnly(True)` disables editing; arrows adjust by 0.1 and Home/End select
0/5. `setStarColor(light, dark=None)` is shared with RatingWidget.
The Home page demonstrates continuous hover previews and click confirmation.

`RoundTabWidget` provides the familiar page-management API of `QTabWidget`, with
an internal `RoundTabBar` and a rounded content frame joined to the selected tab.
The selected tab and content frame are painted as a single silhouette to avoid
gaps or overlapping border pixels at their curved joints. The pages themselves
are ordinary widgets supplied by the application.

```python
from PySide6.QtWidgets import QWidget
from qfluentwidgets_pro import RoundTabWidget, FluentIcon

tabs = RoundTabWidget(window)
tabs.addTab(QWidget(), 'Songs')
tabs.addTab(QWidget(), FluentIcon.FOLDER, 'Albums')
tabs.setCurrentIndex(1)
tabs.currentChanged.connect(on_page_changed)
tabs.tabCloseRequested.connect(tabs.removeTab)
tabs.tabAddRequested.connect(add_page)
```

Supports `addTab(page, label)` / `addTab(page, icon, label)` and corresponding
`insertTab()` overloads, `widget()` / `indexOf()` / `currentWidget()`, selection,
text/icons/tooltips, enabled/visible states, `clear()`, closable/movable tabs and
`setTabBarAutoHide()`. The existing Fluent `(page, label, icon, routeKey)` form
also works. `tabBar()` returns the internal RoundTabBar; attribute-style `tabBar`
remains compatible with this repository's TabWidget. Ctrl+Tab / Ctrl+Shift+Tab
cycle through visible, enabled tabs. Add/close signals are requests only;
`removeTab()` and `clear()` do not delete pages (call `deleteLater()` yourself if
desired). Unlike using a standalone bar, the container synchronizes page order
and selection automatically, including drag reordering and programmatic changes.
`setTabSelectedBackgroundColor(light, dark)` also updates the content background.
This is a top-tab style variant, not a QTabWidget subclass; Qt's alternate tab
positions/shapes and native corner-widget APIs are not provided. It is lightweight,
exported at the package root, and demonstrated on the Buttons page.

`RoundTabBar` is a style variant of the existing `TabBar`: upper rounded corners,
outward-curving bottom corners, a 1px top/side outline with an open bottom, and no
shadow by default. Lower wings are 5px quarter-circle arcs; adjacent tabs share
these wings with 5px overlap, preserving the curve while keeping tabs close.
hover backgrounds extend to their item edges instead of leaving wide side gaps. The bar
is 38 logical pixels high, with 32px tabs, 8px upper corners and a default maximum
tab width of 200px. The bar background is transparent; the surrounding surface
is controlled by the application. In main.py, a light gray demo background makes
the selected tab distinguishable without giving the component a fixed background.
The ordinary TabBar's appearance and behavior are unchanged.

```python
from qfluentwidgets_pro import RoundTabBar, FluentIcon, TabCloseButtonDisplayMode

bar = RoundTabBar(window)
bar.addTab('songs', 'Songs', FluentIcon.MUSIC)
bar.addTab('albums', 'Albums', FluentIcon.FOLDER)
bar.setCurrentTab('albums')
bar.setMovable(True)
bar.setScrollable(True)
bar.setTabMaximumWidth(200)
bar.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.ON_HOVER)
bar.tabCloseRequested.connect(close_page)
bar.tabAddRequested.connect(add_page)
bar.currentChanged.connect(switch_page)
```

Add/close buttons emit requests; the application manages pages and calls
`addTab()` / `removeTab()` as appropriate. Inherited route-key, insertion, data,
icon/text, visibility, enabled-state, drag/`tabMoved` and close-mode APIs remain
available. As with TabBar, programmatic `setCurrentTab()` / `setCurrentIndex()`
updates selection without emitting `currentChanged`; synchronize your page container
explicitly when changing it from application code. For a seamless content edge,
place the bar above the content in a zero-spacing layout and match the content
color with `setTabSelectedBackgroundColor(light, dark)`. The Buttons page demo
includes dynamic pages and movable/scrollable/max-width/close-mode controls.
This lightweight widget is exported at the package root.

`GuideWindow` directly inherits the bundled `qframelesswindow.FramelessWindow`.
It is an independent, modeless wizard shown with `show()` and visible in the Windows
taskbar. Windows 11 enables native Mica by default using the inherited `windowEffect`;
`setMicaEffectEnabled(False)` selects a solid themed fallback (also used on unsupported systems).
It supplies only
the close-only draggable title bar, page container, existing `PipsPager`, and
Previous/Next/Finish footer; each page is an ordinary QWidget supplied by the caller.
The default size is 670x460 logical pixels with an 80px footer, matching the reference.
Page contents, data collection, images, validation messages and persistence are not built in.

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets_pro import GuideWindow, LineEdit

guide = GuideWindow(parent=window)  # Center/lifetime reference only, not a native owner.
page = QWidget()
page_layout = QVBoxLayout(page)
name_edit = LineEdit(page)
page_layout.addWidget(name_edit)
guide.addPage(page)
guide.addPage(QWidget())
guide.finished.connect(save_settings)
guide.cancelled.connect(on_cancel)
guide.show()  # Keep a Python reference to the guide.
```

`addPage(page)` / `insertPage(index, page)` return the page index. `removePage(page)`
hides and detaches the page without deleting it. `count()`, `page(index)`,
`currentPage()`, `currentIndex()` and `setCurrentIndex(index)` manage custom pages;
`currentIndexChanged(int)` reports navigation. Pips, Previous/Next, and the last-page
Finish button stay synchronized. Override `validatePage(page)` to return False
when forward navigation or finish should be refused; `setNextEnabled(False)` also
blocks forward pip jumps. Backward navigation remains available, while
`setCurrentIndex()` is an unconditional application-controlled change.
Use `setStepNavigationEnabled(False)` to disable clickable/keyboard pip navigation.
`finished()` is emitted on successful completion; Esc or the close button emits
`cancelled()` instead. Reopening preserves page state; use `setCurrentIndex(0)`
to restart navigation. `moveToCenter()` centers on the owner/screen.
The optional `parent` is not installed as a Qt/native parent, so it does not hide
the guide from the taskbar; closing the guide does not close the referenced window.
Windows taskbar grouping still follows the application's normal grouping settings.
This lightweight window is root-exported; the Buttons page demo supplies its own
three pages and does not save credentials or contact any service.

`MenuBar` provides compact top-level navigation using existing `RoundMenu` popups.
Titles are 32 logical pixels high; an open menu switches when hovering over another
title. Click the same title or outside the popup, or press Esc, to close it. Alt+the
mnemonic letter (e.g. `&F`) or F10 enables keyboard navigation; arrows, Home/End and
Enter work with separators, disabled items, checkable actions and submenus.

```python
from PySide6.QtGui import QAction
from qfluentwidgets_pro import MenuBar

bar = MenuBar(window)
file_menu = bar.addMenu('File (&F)')  # Also accepts an existing top-level RoundMenu.
open_action = QAction('Open file...', window, shortcut='Ctrl+O')
file_menu.addAction(open_action)
file_menu.addSeparator()
file_menu.addAction(QAction('New file...', window))
bar.triggered.connect(handle_action)  # Receives the triggered QAction.
layout.addWidget(bar)
```

Menu action shortcuts are registered while their menu belongs to a visible,
enabled bar in the active window (not system-wide). Disabled/hidden menu headers
do not activate their shortcuts. `insertMenu(before, menu)`, `removeMenu(menu)` and
`clear()` manage navigation without deleting reusable menus. `setActiveMenu(menu)`
opens a menu, `setActiveMenu(None)` / `closeActiveMenu()` closes it, and
`activeMenuChanged(menu_or_none)` reports changes. Native QWidget action methods
also support direct command headers. This lightweight widget is exported at the
package root and is demonstrated at the top of the Buttons page.

`WaitingDialog` shows a compact, centered waiting panel with a window-modal mask,
an accent-colored `IndeterminateProgressRing`, title and description. The reference
panel is 300x132 logical pixels with a 56px ring; text wraps and increases its height
when needed. It has no footer buttons: press Esc to cancel, or complete it with `accept()`.

```python
from qfluentwidgets_pro import WaitingDialog

dialog = WaitingDialog('Please wait...', 'Preparing the download...', parent=window)
dialog.rejected.connect(cancel_task)  # If the worker itself should be canceled.
dialog.open()  # Non-blocking; keep the dialog alive while your worker runs.
# Update from the GUI thread via worker signals:
# worker.statusChanged.connect(dialog.setContent)
# worker.finished.connect(dialog.accept)
```

`setTitle()` / `setContent()` update the text; `title()` / `content()` return it.
Use `accepted`, `rejected` or `finished(int)` for the result. Esc does not itself
terminate a worker: connect cancellation explicitly. Run long tasks outside the
GUI thread to keep the ring and Esc responsive. The ring stops when closing starts
and resumes when a retained dialog is opened again. A parent window is required;
the mask follows its resize/move and closes when it hides. Outside clicks do not
cancel by default. This lightweight component is exported from the root package;
the Buttons page includes an Esc-cancelable example.

`ShortcutPicker` uses a clickable `CardWidget` with separate accent-colored key caps.
Click anywhere (including key caps, gaps and the pencil icon) to open its masked
capture dialog; Enter / Space also open it when focused. Save commits the draft, Reset restores
the configured default in the draft, and Cancel leaves the current shortcut unchanged.

```python
from PySide6.QtGui import QKeySequence, QShortcut
from qfluentwidgets_pro import ShortcutPicker

picker = ShortcutPicker('Ctrl+Shift+A', parent=window)
picker.setDefaultKeySequence('Ctrl+Shift+A')
picker.setDialogTitle('Activate shortcut')
picker.keySequenceChanged.connect(lambda seq: print(seq.toString(QKeySequence.PortableText)))
# Register it explicitly if your application needs an action:
shortcut = QShortcut(picker.keySequence(), window)
picker.keySequenceChanged.connect(shortcut.setKey)
shortcut.activated.connect(your_action)
```

`keySequence()` and `defaultKeySequence()` return copies. `setKeySequence()` accepts
a QKeySequence, QKeyCombination, Qt key or PortableText string; only one combination
is supported (multi-stroke and invalid inputs raise errors without changing state).
`clear()` unsets the shortcut and `reset()` restores the default immediately.
`keySequenceChanged(QKeySequence)` reports changes; `keySequenceSelected(QKeySequence)`
and `editingFinished()` fire on every Save, including an unchanged value;
`editingCanceled()` reports cancellation. `showEditor()` / `cancelEditing()` control
the editor, and `setDialogDescription()` changes its instruction.

Modifier-only keys (including Meta), function keys and numpad keys are supported.
Escape cancels by default; `setEscapeCancelsCapture(False)` lets it be recorded,
with cancellation through the button. Enter, Space and Tab are captured, not treated
as dialog button commands. Capturing suppresses application shortcuts until the
editor closes, but does not install global keyboard hooks or intercept OS-reserved
combinations. Registering modifier-only shortcuts is subject to Qt/OS limitations.
This pure QtWidgets component is exported from the root package; the Buttons page
includes a localized editor and an explicitly registered test shortcut.

`CircleColorPicker` selects a color from a customizable row of circular swatches.
The selected swatch has a thin, same-color outline separated by a transparent gap.
It does **not** modify or bind to the application accent color; `colorChanged(QColor)`
only reports the selected color. The background stays transparent in both themes.

```python
from qfluentwidgets_pro import CircleColorPicker

picker = CircleColorPicker(['#FF4343', '#FFB900', '#107C10'])
picker.setColor('#FFB900')
picker.colorChanged.connect(lambda color: print(color.name()))
```

`setColors(iterable)` replaces the palette, `addColor()` / `addColors()` append,
and `colors()` returns copies. `setColor()` requires an existing palette color;
`setCurrentIndex()` selects by position, with `-1` clearing the selection.
`color()`, `currentIndex()` and `count()` expose the state. Empty palettes return
an invalid QColor. Replacement preserves the selected color if present, otherwise
selects the first swatch. Duplicate colors are allowed; `currentIndexChanged(int)`
reports a different swatch even when its color equals the previous one.
Only actual color/index changes emit signals. Arrows and Home/End navigate;
Space/Enter select. The Colors demo allows editing the palette without changing
the application accent. This pure QtWidgets component is exported from the root
package and needs no optional heavy dependencies.

`DropDownColorPicker` provides a compact, confirmable color editor: a hue/saturation
square, brightness slider, RGB/HSV selector, hexadecimal input and RGBA/HSVA fields
with color-gradient sliders. It reuses the existing dropdown button QSS, Flyout,
Fluent inputs and animated slider handles. Gradient rendering is pure Qt.

```python
from qfluentwidgets_pro import DropDownColorPicker

picker = DropDownColorPicker('#0078D4', parent=window)
picker.colorChanged.connect(lambda color: print(color.name(color.HexArgb)))
picker.setAlphaEnabled(True)  # enabled by default
```

`setColor()` / `color()` set or return a copy of the committed 8-bit QColor.
Dragging or typing edits a draft and emits `colorPreviewed(QColor)`, without changing
the button's committed color. The checkmark confirms, emitting `colorChanged(QColor)`
only for actual changes and `colorSelected(QColor)` for every confirmation.
The cross, Escape or an outside click discards the draft and emits `pickingCanceled()`.
`showPicker()` / `closePicker()` control the flyout. Hex accepts `#AARRGGBB` or
six-digit `#RRGGBB` (which preserves draft alpha). RGB channels and alpha use 0–255;
HSV uses hue 0–359 and saturation/value 0–100. Hue is retained through grayscale
and zero brightness so restoring saturation/value does not unexpectedly become red.
Invalid or incomplete edits cannot introduce an invalid color. `isAlphaEnabled()`
reads the setting; disabling alpha closes any active draft, hides the alpha row and
normalizes the committed color to opaque. The footer remains visible on smaller
screens while the editor body scrolls. Selecting colors never changes the app accent.
This lightweight root export is demonstrated on the Colors page and needs no
Pillow, NumPy, QtMultimedia or other optional heavy modules.

`DropDownColorPalette` is a standard-QSS dropdown button with Automatic, 60 theme
swatches (six rows of ten), ten standard colors, and More Colors. The panel uses
the existing Flyout; clicking outside or pressing Escape closes without changing
the color. More Colors closes the palette and opens the existing
[ColorDialog](https://pyqt-fluent-widgets.readthedocs.io/zh-cn/latest/autoapi/qfluentwidgets/components/dialog_box/color_dialog/index.html).
Only accepting that dialog commits its color; canceling keeps the original.

```python
from qfluentwidgets_pro import DropDownColorPalette

picker = DropDownColorPalette('#0078D4', parent=window)
picker.colorChanged.connect(lambda color: print(color.name()))
picker.setAutomaticColor('#000000')
picker.setAlphaEnabled(True)  # optional alpha controls in More Colors
```

`setColor()` / `color()` accept and return QColor-compatible values / copies.
`colorChanged(QColor)` reports actual changes, while `colorSelected(QColor)` reports
every user confirmation, including an unchanged color. `setAutomatic()` selects
the explicit automatic color; `automaticColor()`, `isAutomatic()` and
`automaticChanged(bool)` expose that mode. Automatic defaults to black and does
not depend on the application accent or light/dark theme. `showPalette()` /
`closePalette()` and `showColorDialog()` control the popups; `isAlphaEnabled()`
reads the optional dialog alpha setting (off by default). Arrows and Home/End move
keyboard focus through the swatches; Space/Enter confirms. Theme Colors are palette
presets, **not** a binding to the application's accent. Invalid colors are rejected
without changing state. The lightweight component is exported from the root
package and demonstrated on the Colors page.

`ScreenColorPicker` is a compact color swatch / eyedropper button. Click it or
call `startPicking()` to preview screen colors in a floating swatch + hexadecimal
card; left-click or Enter/Space confirms, Escape or right-click cancels without
changing the committed color. It never binds to or modifies the application accent.

```python
from qfluentwidgets_pro import ScreenColorPicker

picker = ScreenColorPicker('#0078D4')
picker.setFreezeScreenEnabled(False)  # Windows live capture; True freezes the view
picker.colorChanged.connect(lambda color: print(color.name()))
```

Use `setColor()` / `color()` for the committed QColor. `colorChanged(QColor)`
reports actual changes, `colorPicked(QColor)` reports every confirmation, and
`colorHovered(QColor)` reports previews only. `isPicking()`, `pickingChanged(bool)`,
`cancelPicking()` and `pickingCanceled()` expose the session lifecycle.
The button inherits PushButton and its QSS for normal/hover/pressed/disabled
backgrounds and borders, with a standard 32px height.
`setFreezeScreenEnabled(True/False)` chooses frozen/live capture;
`isFreezeScreenEnabled()` reads the setting. Freezing defaults to True.
Changing mode during a session cancels that session without changing the color.
Frozen mode captures screens once into memory before overlays appear. Live mode
uses transparent overlays and samples the current pixel at about 30Hz, including
when the pointer stays still; confirming samples again rather than using a stale
preview. Live overlays and their cards are excluded from capture using Windows
display affinity, not redrawn screenshots. Live mode requires Windows 10 version
2004 or newer with the native Qt Windows backend. On unsupported platforms or if
capture exclusion fails it reports an error; it never silently freezes or returns
an overlay-contaminated color. The Windows bridge is standard-library ctypes,
loaded only when starting live mode. See Microsoft's
[SetWindowDisplayAffinity documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity).
Each screen has its own overlay and logical-to-physical pixel mapping, including
negative monitor origins and mixed DPI. Screenshots are released at session end
and are never written to files. Disabling/hiding the picker, deactivating the app,
or changing the monitor layout cancels picking. Only one picker session can run
at a time. Capture failure emits `errorOccurred(str)` and leaves the color intact.
OS screen recording permissions and platform capture restrictions still apply;
protected content may be blank and Qt grabWindow may be unavailable on Wayland.
The Colors demo includes screen picking, a freeze checkbox and error messages. The component is
exported from the root package, using QtGui/QtWidgets only (no Pillow, NumPy or
QtMultimedia). Qt's capture and high-DPI behavior are documented in
[QScreen::grabWindow](https://doc.qt.io/qt-6/qscreen.html#grabWindow).

`CodeEdit` is a native QPlainTextEdit-based editor with line numbers, current-line
highlight, indentation and 20 language lexers. Install its optional dependency:

```bash
python -m pip install -r requirements-codeedit.txt
```

```python
from qfluentwidgets_pro.components.widgets.code_edit import CodeEdit, CodeLanguage
editor = CodeEdit(language=CodeLanguage.JSON)
editor.setPlainText('{"enabled": true}')
editor.setLanguage("python")  # changes highlighting, not the code
editor.setIndentSize(4)
editor.setLineNumbersVisible(True)
```

Languages: Python, C, C++, C#, Java, JavaScript, TypeScript, JSON, HTML, CSS,
XML, YAML, TOML, INI, Bash, PowerShell, SQL, Go, Rust and Markdown.
Full-document Pygments lexing preserves multiline/embedded syntax and runs in
a worker; only changed lines receive batched Qt formats. Stale revisions are
discarded. Documents above 1,000,000 characters remain editable without highlighting;
`highlightingFailed` reports this limit or lexer errors. This is not an IDE: completion,
folding, diagnostics and file saving are not included. The CodeEdit demo lets you
switch language, load examples, toggle read-only/line numbers and change themes.

`AvatarPicker` extends AvatarWidget: hovering displays a dark overlay and a white
camera icon; clicking selects an image and opens the shared circular ImageCropper.
Confirmation updates the avatar and emits `imageChanged(QImage)`; cancellation
preserves it. Use `setRadius()` for size or `cropImage(image)` to skip file selection.
The Magnifier page includes an avatar picker example.

`ImageCropper(image, parent)` provides draggable crop bounds, rotation and horizontal
flip. `imageCropped` returns a QImage on confirmation; cancellation leaves the caller's
preview unchanged. `setCropShape(CropShape.CIRCLE)` enables a circular mask, and
`setCropPathFactory(factory)` supports custom QPainterPath shapes. The shape toolbar
button is disabled, matching the reference gallery. No save/export UI is included.

`ImageMagnifierWidget` extends ImageLabel with a cursor-following circular lens,
accent-colored border and crosshair. Set the zoom with `setMagnification(2.0)`,
the lens radius with `setRadius(50)`, or disable it with `setMagnifierEnabled(False)`.
It supports ImageLabel image/scaling APIs and keyboard arrow movement when focused.
The Magnifier demo page includes 2×, 3× and 4× zoom.

`RangeCalendarPicker` reuses CalendarPicker's scrolling calendar;
`FastRangeCalendarPicker` reuses FastCalendarPicker's compact paged calendar and
`setFlyoutAnimationType()`. Click a start date, hover to preview, then click an end
date to commit. Endpoints have accent rings and the inclusive range has a neutral
row-spanning fill. Reverse selection is sorted; same-day and cross-month/year
ranges are supported. Dismissing with Escape or an outside click preserves the
committed range. `setResetEnabled(True)` enables the existing reset action.

```python
from PySide6.QtCore import QDate
from qfluentwidgets_pro import RangeCalendarPicker, FastRangeCalendarPicker

picker = FastRangeCalendarPicker()
picker.setDateRange(QDate(2024, 3, 13), QDate(2024, 3, 21))
picker.setDateFormat('yyyy-MM-dd')
picker.rangeChanged.connect(lambda start, end: print(start, end))
start, end = picker.dateRange()  # also read-only startDate / endDate properties
```

Both support `reset()` (emits an invalid QDate pair when clearing a selection).
`setDate(date)` selects a single-day range. The Buttons page shows both variants.
By default all weekdays are selectable. Before opening a calendar, use
`setDisabledWeekDays({6, 7})` to disable weekends (Monday=1, Sunday=7): disabled
days are dimmed/struck out and cannot be range endpoints, but may lie inside a
range. Changing this setting clears a committed range if an endpoint becomes
disabled. The demo enables this option and keeps the reset action hidden.

`CalendarTimePicker` combines the original scrolling calendar and the existing
24-hour time wheels in one popup; `FastCalendarTimePicker` uses the fast paged
calendar. A shared confirm/cancel footer commits date and time together. Selecting
a date or scrolling a wheel only changes the draft; Cancel, Escape and outside
clicks preserve the committed value. Enter confirms. Both are lightweight root exports.

```python
from PySide6.QtCore import QDate, QDateTime, QTime
from qfluentwidgets_pro import CalendarTimePicker, FastCalendarTimePicker

picker = FastCalendarTimePicker()
picker.setDateTime(QDateTime(QDate(2026, 2, 10), QTime(20, 0, 0)))
picker.setDateTimeFormat('yyyy-MM-dd HH:mm:ss')
picker.dateTimeChanged.connect(lambda value: print(value))
value = picker.dateTime  # QDateTime copy; date / time properties are also available
```

Seconds are visible by default. `setSecondVisible(False)` hides that wheel and
switches the default display to minutes; confirming this mode sets seconds to 0.
Custom formats are retained. `setDate()` / `setTime()` preserve the other part,
and midnight is valid. Date-time timezone information is preserved during editing.
`setResetEnabled(True)` shows the calendar reset action; `reset()` clears the
selection and emits an invalid QDateTime. `dateChanged` / `timeChanged` emit only
when their part changes. Both support `setFlyoutAnimationType()` and appear on
the Buttons demo page.

`AudioWaveformWidget` is a transparent, pure QtWidgets sample waveform view. It
does not import QtMultimedia, NumPy or an audio decoder and is exported from the
package root. Round-cap bars retain each time bucket's min/max amplitudes; silence
becomes center dots. Played/unplayed portions have separate light/dark colors.
Completed sample blocks and visible geometry are cached; position changes do not
rescan PCM. No sound is played by the widget itself.

```python
from qfluentwidgets_pro import AudioWaveformWidget

waveform = AudioWaveformWidget()
waveform.setSamples(samples, sampleRate=24000)  # normalized mono numbers, -1..1
waveform.appendSamples(chunk, sampleRate=24000)  # optional streamed TTS chunks
player.positionChanged.connect(waveform.setPosition)  # milliseconds
waveform.seekRequested.connect(player.setPosition)
```

`setSamples()` resets position; `appendSamples()` preserves absolute position and
amplitude scale, fits the currently available recording, and requires a consistent
sample rate until `clear()`. Nonfinite samples are rejected; finite out-of-range
samples are clipped. Inputs are copied. Setters must run on the GUI thread (use
queued signals from workers). Configure `setBarWidth()`, `setBarSpacing()`,
`setAmplitudeScale()`, `setWaveformColor(light, dark)` and
`setPlayedColor(light, dark)`. Mouse click/drag and Left/Right (1 second), Home/End
request seeking; `setSeekEnabled(False)` disables interaction. `duration()` and
`position()` use milliseconds. The Waveform page lets you select a local audio
file, decodes its waveform incrementally, and supports actual play/pause/stop and
seeking. It explicitly imports the optional decoder and QtMultimedia player;
these dependencies remain absent from the widget's own import path.
"Load test WAV" opens `gallery/resource/audio/waveform_sample.wav`: a five-second,
24 kHz, mono, 16-bit PCM synthetic test sound, not speech. To generate another copy:
`python examples/audio_waveform/generate_sample.py --output test.wav` (no overwrite).
On Windows, `main.py` defaults the gallery to the native multimedia backend when
its plugin is installed, avoiding a locally reproduced FFmpeg output-layout error.
An explicit `QT_MEDIA_BACKEND` is respected. The library itself never selects a
backend; format support still depends on the selected backend. The gallery build
includes multimedia plugins and the test WAV as data.

`AudioDecoder` is a separate **heavy, opt-in helper**, never exported by any
`__init__.py`. Import its exact module only when file decoding is needed:

```python
from qfluentwidgets_pro.common.audio_decoder import AudioDecoder

decoder = AudioDecoder(parent=waveform)  # keep it alive throughout decoding
decoder.decoded.connect(waveform.setSamples)
decoder.errorOccurred.connect(print)
decoder.decode('speech.wav')
# For incremental display instead: clear the widget before EACH decode, connect
# decoder.samplesReady to waveform.appendSamples, and omit the decoded connection.
```

The helper uses Qt's [QAudioDecoder](https://doc.qt.io/qt-6/qaudiodecoder.html)
asynchronously, copying UInt8/Int16/Int32/float PCM into normalized float arrays.
Multichannel frames retain the strongest channel, avoiding anti-phase cancellation;
the result is waveform data, not a playback downmix. `samplesReady(samples, rate)`
emits chunks; `decoded(samples, rate)` emits the complete result, then `finished()`.
It retains the recording in memory. `stop()` cancels without a completion signal;
`decode()` cancels/replaces any previous request. Errors are reported through
`errorOccurred`. Available file formats depend on the Qt backend/codecs, not a
guarantee that every MP3/AAC file is supported.

`FilledPushButton` and `FilledToolButton` use Fluent semantic colors for light-theme
resting fills (neutral, success, caution and critical). Attention follows the accent
color; the existing dark palette and translucent hover/pressed fills are preserved.

`FlyoutDialog` provides custom flyout content with confirm/cancel icon buttons.
Its compact footer is 40 logical pixels tall with full-half-width hover targets,
no button tooltips and a 2-pixel divider. Wrapped content is sized at the popup width.
Call `addWidget()` to add controls and `showAt(target, parent)` to display it.
Connect `accepted` / `rejected` for the result; outside dismissal is cancellation.
It reuses Flyout positioning, shadows and animations, and is deleted on close.
The Buttons page includes a Show dialog example.

`TimeLineWidget` displays grouped timeline cards with status icons and connector
lines. Use `addGroup(title, InfoBarIcon.SUCCESS)` then `group.addItem(text, icon)`.
Cards support wrapped/rich text; groups and items can be removed dynamically.
Each `TimeLineItem` inherits `CardWidget`, reusing its background, borders and
hover/pressed animation. The entire item (icon, text and padding) is clickable:
connect `item.clicked` to your action. Enter / Space activate a focused card;
`setClickEnabled(False)` disables activation without removing its contents.
The default maximum width is 370 logical pixels (328px cards); single-line items
are 50px high and adjacent items have a 19px gap. Wrapped text grows vertically.
Use `setMaximumWidth()` / `setFixedWidth()` to customize the timeline width.
The TimeLine demo page shows completed, scheduled and pending tasks.

`FilledFluentWindow` provides an expanded sidebar with accent-filled selection
and a search box. It supports the same `addSubInterface()` and `switchTo()` APIs
as `FluentWindow`. The search box automatically searches registered page names;
click a result or use the arrow keys and Enter to navigate. Escape dismisses
the results, and clearing the query keeps the current page unchanged.
Run `main.py` and click "打开 FilledFluentWindow 窗口" on the home page to preview
navigation, search, theme switching, and custom accent colors.

## Optional imports and Nuitka packaging

Some widgets deliberately do **not** appear in the package's `__init__.py`
exports. This is not a missing implementation: importing a unified entry point
can put unused optional dependencies into Nuitka's compilation graph. Import
these features from their specific modules only when your application uses them.

| Optional feature | Explicit import module | Dependencies |
| --- | --- | --- |
| `ChartWidget` | `qfluentwidgets_pro.components.widgets.chart_widget` | QtWebEngine, QtQuickWidgets and related Qt runtime libraries |
| `CodeEdit`, `CodeLanguage` | `qfluentwidgets_pro.components.widgets.code_edit` | Pygments lexers |
| `ChatWidget`, `ChatMessage` | `qfluentwidgets_pro.components.widgets.chat_widget` | Optional Pygments / Matplotlib formulas; no WebEngine |
| Acrylic widgets | `qfluentwidgets_pro.components.material` or `qfluentwidgets_pro.components.widgets.acrylic_label` | Optional CPU blur: NumPy, SciPy, Pillow, colorthief |
| Media playback widgets | `qfluentwidgets_pro.multimedia` | QtMultimedia / QtMultimediaWidgets |
| `AudioDecoder` (waveform file decoding only) | `qfluentwidgets_pro.common.audio_decoder` | QtMultimedia and its backend/codecs; not needed by `AudioWaveformWidget` |
| `FramelessWebEngineView` | `qfluentwidgets_pro.qframelesswindow.webengine` | QtWebEngineWidgets |

```python
from qfluentwidgets_pro import PushButton, RadialGauge  # lightweight exports
# Import only the optional feature your app needs:
from qfluentwidgets_pro.components.widgets.code_edit import CodeEdit, CodeLanguage
from qfluentwidgets_pro.components.widgets.chart_widget import ChartWidget
```

Constructor-time imports and `try/except ImportError` are runtime behavior, not
a guarantee that Nuitka will omit those dependencies. Standalone mode follows
imports by default; `--nofollow-import-to` can exclude unwanted modules, but
attempting to use an excluded feature can fail. See the
[Nuitka standalone documentation](https://nuitka.net/user-documentation/use-cases.html#standalone-program-distribution).

**Acrylic exception:** navigation still imports Acrylic helpers indirectly.
On a source installation with its optional dependencies installed, even importing
the package root can therefore load NumPy/SciPy/Pillow/colorthief. For a build
without CPU Acrylic blur, exclude `qfluentwidgets_pro.common.image_utils` as well
as NumPy/SciPy. The existing fallback preserves navigation and displays an
unblurred image; this does not disable the native Windows Mica effect.

```text
--nofollow-import-to=qfluentwidgets_pro.common.image_utils
--nofollow-import-to=numpy
--nofollow-import-to=scipy
```

`deploy.py` builds the **complete gallery in `main.py`**, which explicitly imports
charts, CodeEdit, audio waveform and native chat demos, including QtMultimedia
for playback and Matplotlib/NumPy for offline chat formulas. CPU Acrylic blur
remains excluded independently. It deliberately includes Pygments for dynamic
lexer discovery and is not a minimal business-app build template. Use your own entry
point to avoid gallery-only imports; omit `--include-package=pygments` when not
using CodeEdit. If you do use CodeEdit, include its dynamically loaded lexers.
Final bundle contents must be checked in Nuitka's compilation report and output;
removing a root export alone does not guarantee removal of Qt plugins or native
libraries reached through other imports. `RadialGauge` is pure QtWidgets and is
exported normally; it was an accidental omission, not a heavy dependency.

## 📁 Project Structure

- `qfluentwidgets_pro/`
  - Main package (free base + restored components)
- `main.py`
  - Demo / playground
- `docs/`
  - Documentation assets

## Exclusive toolbox

`ToolBox` stacks native rounded tool panels. The entire header is clickable;
opening a panel closes the previous one, preserving its controls and values.
Only the arrow area gains a small rounded hover background, not the entire header.

```python
from qfluentwidgets_pro import ToolBox

tools = ToolBox(self)
tools.addItem(blendPage, "Blend")  # arbitrary QWidget; first item opens
tools.addItem(huePage, "Hue")
tools.addItem(sharpenPage, "Sharpen")
tools.setCurrentIndex(1)
tools.currentChanged.connect(self.onToolChanged)
```

Clicking the active header or `setCurrentIndex(-1)` collapses all panels.
Expansion/collapse animate over 200 ms each. When switching pages, the old page
finishes collapsing before the new one opens, so two bodies never appear at once.
Rapid clicks replace the pending destination; reopening a closing page reverses
from its current height. `setAnimationDuration(0)` disables/settles animations.
`currentChanged` reports the requested selection when the transition starts;
the selected page may still be waiting for the old page to close.
`addItem(widget, text, icon=None)` / `insertItem(index, widget, text, icon=None)`
support optional icons. `count()`, `widget()`, `indexOf()`, `currentWidget()`,
`itemText()` / `setItemText()`, `itemIcon()` / `setItemIcon()` and
`setItemEnabled()` manage pages. `removeItem(index)` returns a hidden, detached
page without deleting it. Disabling/removing the active page selects another
enabled page, or collapses all when none remain. `currentChanged(int)` reports
the current index (`-1` means all collapsed). Header buttons support Space/Enter;
`itemHeader()` exposes them for tooltips. Place the toolbox in a `ScrollArea`
when content can exceed the available height. The **ToolBox** demo has blend,
hue and sharpen panels with independent, persistent controls.

## Dashboard feature card

`DashboardCardWidget` inherits `SimpleCardWidget`, retaining its rounded border,
theme-aware default fill and native painting. The header contains an optional
icon, a title and a text-free switch. Add descriptive text or your own widgets:

```python
from qfluentwidgets_pro import DashboardCardWidget, FluentIcon, PushButton

card = DashboardCardWidget(FluentIcon.GLOBE, "Hosts editor", parent=self)
card.setCardBackgroundColor("#edf7fa", "#282e30")  # light / dark
card.addWidget(PushButton("Open editor", card))
card.checkedChanged.connect(self.onFeatureToggled)
card.setChecked(True)
```

`setTitle()`, `setContent()` and `setIcon()` update caller-provided values.
`setIcon(None)` / `setSwitchVisible(False)` hide the optional header controls.
`addWidget()` / `addLayout()` append arbitrary content via `viewLayout`.
`resetCardBackgroundColor()` restores the inherited translucent background;
with one color, `setCardBackgroundColor()` uses it for both themes. `setChecked()`
and user toggles emit `checkedChanged(bool)` only when the state changes.
Switching does not disable custom content or implement business logic.
The **DashboardCard** demo includes text, custom-button and default-fill cards.

## Four-direction drawer

`Drawer` slides custom QWidget content over a parent content area, with a native
edge shadow, header and close button. It is not a separate window:

```python
from qfluentwidgets_pro import Drawer, DrawerPosition, BodyLabel

self.drawer = Drawer("Notifications", self.contentWidget)
self.drawer.addWidget(BodyLabel("No notifications", self.drawer.contentWidget))
self.drawer.setDrawerSize(320)  # width for left/right, height for top/bottom
self.drawer.open(DrawerPosition.RIGHT)  # LEFT / RIGHT / TOP / BOTTOM
# self.drawer.close()  # animated; hide() is immediate
```

Do not add the overlay to the parent's layout. `viewLayout` accepts your own
widgets/layouts and content is retained after closing. Parent resize updates the
panel geometry, even mid-animation. Default dismissal is via close button, Esc
or left-clicking the mask; `setEscClosable()` / `setClosableOnMaskClicked()` can
disable either path. Outside clicks are consumed, Tab stays inside the panel,
and closing restores the previous focus. Parent hide dismisses without reopening
on the next show. `opened`/`closed` fire after the transition completes;
`isOpen()` becomes false when closing starts. `setAnimationDuration(0)` disables
animation, `setMaskColor()` customizes the shade, and `shadowEffect` exposes the
native shadow settings. The **Drawer** demo covers all four directions.

## Text watermark overlay

`Watermark` attaches to a target QWidget, repeats rotated plain text and follows
the target's size. Do not add it to the target's layout:

```python
from qfluentwidgets_pro import Watermark, getFont

self.watermark = Watermark("Internal · Alice · ID 1001", self.contentWidget)
self.watermark.setAngle(-15)  # negative = counterclockwise, positive = clockwise
self.watermark.setOpacity(0.1)  # 0..1
self.watermark.setSpacing(60, 30)  # horizontal/vertical gaps, logical pixels
self.watermark.setFont(getFont(18))
# Optional custom light/dark colors (defaults: black/white).
self.watermark.setColor("#444444", "#dddddd")
self.watermark.hide()  # show() restores it
```

Input, clicks and scrolling pass through to underlying controls. New or raised
target children are tracked to keep the watermark on top. Use
`setTargetWidget(otherWidget)` to retarget, or `setTargetWidget(None)` to detach
and hide. For stationary watermarks over scrollable content, target the scroll
area's `viewport()`. Text may contain newlines and is never translated or parsed
as HTML. The native tiled pixmap is cached and regenerated for font, color,
rotation, text, spacing or device-pixel-ratio changes. Only the target surface is
covered; this is not a tamper-proof security feature and does not modify or
automatically watermark exported images/PDFs. The **Watermark** demo includes
real controls underneath the overlay and live appearance settings.

## Loading skeletons

`ArticleSkeleton`, `CirclePersonalInfoSkeleton` and `RectanglePersonalInfoSkeleton`
provide the article and avatar/text layouts. `SkeletonWidget` accepts custom
shapes or an overridden `skeletonPath()`, with no heavy dependencies:

```python
from PySide6.QtCore import QRectF
from qfluentwidgets_pro import SkeletonWidget, CirclePersonalInfoSkeleton

profile = CirclePersonalInfoSkeleton(parent)
custom = SkeletonWidget(parent)
custom.addEllipse(QRectF(0, 0, 100, 100))
custom.addRect(QRectF(.25, .1, .7, .3), relative=True)
custom.addRect(QRectF(.25, .6, .7, .3), relative=True)
custom.setAnimationDuration(1500)  # milliseconds per sweep
custom.setAnimationEnabled(False)  # static placeholders
```

The brighter native sweep leans 30 degrees clockwise from vertical and moves
left to right, clipped to the shapes; gaps remain
transparent and all shapes in a widget share one animation. Hidden widgets pause
and resume on show. `setColors(baseLight, baseDark, highlightLight, highlightDark)`
customizes both themes; neutral defaults are independent of the accent color.
Use normal Qt layouts/geometry to size the canvas. Remove or hide the skeleton
when real content is ready; it does not fetch data or automatically replace it.
The **Skeleton** demo page includes all four layouts and an animation toggle;
its custom layout keeps a 20-pixel avatar/text gap as the window widens.

## Native ChatWidget

`ChatWidget` is a QQ-style, **native QtWidgets** conversation view and composer,
not a WebView. Incoming messages have left-hand avatars/names/bubbles; outgoing
messages are right-aligned. Markdown uses QTextDocument with raw HTML disabled.
Fenced code has a copy button and reuses CodeEdit's asynchronous highlighting.
Unknown languages or missing Pygments fall back to readable plain code.

```python
from qfluentwidgets_pro.components.widgets.chat_widget import ChatWidget

chat = ChatWidget(parent)
chat.addToolButton(FluentIcon.PHOTO, "Attach image", choose_image, side="left")
chat.addToolButton(FluentIcon.HISTORY, "Latest", chat.scrollToBottom, side="right")
chat.sendRequested.connect(on_send)  # caller adds/sends the message
chat.addMessage("Hello", role="user", name="Me", avatar="me.png")
reply = chat.addMessage("", name="Assistant", streaming=True)
chat.appendText(reply, "**Hello!**")
chat.finishMessage(reply)
```

`addToolWidget()` accepts arbitrary widgets on either side. `addImageMessage()`
accepts local images/QImage/QPixmap, while `addWidgetMessage()` embeds a custom
file/voice/task card. Streams are coalesced every 40 ms and reuse unchanged
content blocks. History follows the bottom only while the user is near it;
scrolling up pauses following and shows a compact down-arrow RoundToolButton
(tooltip: **Jump to latest**), with an opaque circular backing so messages cannot
show through its translucent surface. Hover over the thin divider to highlight
it and drag vertically to resize history/composer; neither area can collapse.
The editor expands with the composer. `chat.splitter.setSizes([460, 184])` can
set initial heights; `setComposerVisible()` preserves the split when toggled.
`setBusy(True)` shows
a Stop button that emits `stopRequested`; the caller owns backend cancellation.
Enter sends; Shift+Enter inserts a newline. `setSendOnEnter(False)` selects
Ctrl+Enter sending. IME composition is not submitted by Enter.

Per-message action bars are opt-in and apply to existing and future rows:

```python
chat.setMessageToolBarEnabled(True)
chat.messageActionTriggered.connect(on_message_action)  # (actionId, messageId)
chat.addMessageAction("inspect", FluentIcon.INFO, "Inspect", inspect_message,
                      roles="assistant", kinds="text")  # callback(messageId)
```

Assistant text gets Copy / Retry / Like / Dislike / Read aloud / Share buttons;
user text and images get Copy / Share, and custom widget cards get Share. Only
Copy performs a local action (original text or image to the clipboard). Other
buttons emit an event, without implementing model retries, speech or sharing.
Use `removeMessageAction()` / `clearMessageActions()` to customize defaults;
`messageActionButton(messageId, actionId)` exposes each row's button for host
enabled/checkable states. Labels passed by callers are not translated. Hiding
bars removes their layout space and keeps short bubbles compact; narrow bars
wrap rather than overflow. The demo includes a message-toolbar checkbox.

Install `pip install -r requirements-chat.txt` for code highlighting and offline
MathText formulas (`$...$`, `$$...$$`, `\(...\)`, `\[...\]`). Formula support is a
LaTeX **subset**, not an external TeX engine; unsupported expressions remain
visible and emit `renderWarning`. It imports Matplotlib only when a complete
formula is encountered. `setMathEnabled(False)` disables it, and
`setFormulaRenderer(callable)` accepts a provider `(expression, color, pointSize)`
returning a QImage. No WebEngine/JavaScript, network client, automatic link opening
or implicit local/network Markdown-image loading is involved.

All update APIs run on the GUI thread; connect worker chunk signals to
`appendText(str, str)` using a queued connection. Message ids are stable;
`message()`/`messages()` return immutable snapshots. `clear()` retains drafts and
tools. This first version uses one widget row per message (no large-history
virtualization), and does not implement persistence, upload/recording, full LaTeX,
tool execution or an AI adapter. The `Chat` page in `main.py` demonstrates local
simulated streaming and custom tools.

## Translation and resource builds

Component source strings are English literals wrapped in `tr()`. Update
`qfluentwidgets_pro/_rc/i18n/qfluentwidgets.en_US.ts`, then run:

```powershell
py -3.9 scripts/translate_ts.py --all --jobs 4 --build
```

This preserves existing translations, adds missing template messages, translates
only pending entries in batches of 50, compiles all QM catalogs, and rebuilds the
widget, gallery and frameless-window resource modules. Completed batches are saved
for resuming a failed run. Placeholders and file-filter wildcards are checked.
Use `--all --skip-translate` to sync without API calls, or
`--compile-qm --compile-resources` to rebuild already translated files.
The API key comes from `DEEPSEEK_API_KEY` or the ignored local
`scripts/translate_ts.local.json` file (`{"api_key": "..."}`); never commit it.

## ⚠️ Disclaimer

- This is a **community-driven restoration/extension** project.
- This repository is **not affiliated with** the official QFluentWidgets Pro team.
- Please respect the original project's license and commercial terms.

## 🧮 Acknowledgments

- `Pager` `DropMultiFilesWidget` `DropSingleFileWidget` `Splitter` `PinBox` `LabelLineEdit` `Toast` component implementation references [PySide6-Fluent-UI](https://github.com/HiyorinI/PySide6-Fluent-UI) by HiyorinI

## 🗺️ Roadmap

- Improve widget API consistency and documentation
- Restore more Pro widgets/components (prioritized by community needs)
- Add more examples and screenshots

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 🏆 Contributors

<a href="https://github.com/Fairy-Oracle-Sanctuary/PySide6-Fluent-Widgets-Pro/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Fairy-Oracle-Sanctuary/PySide6-Fluent-Widgets-Pro&v=2" />
</a>
