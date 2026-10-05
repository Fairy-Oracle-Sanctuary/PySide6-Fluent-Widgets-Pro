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

67 components have been restored or extended in this repo (the list will be updated continuously):

`HyperlinkToolButton` `FilledPushButton` `FilledToolButton`
`TextPushButton` `TextToolButton` `LuminaPushButton`
`IndeterminateProgressPushButton`
`ProgressPushButton`
`TimeLineWidget`
`FlyoutDialog`
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

`FlyoutDialog` provides custom flyout content with confirm/cancel icon buttons.
Call `addWidget()` to add controls and `showAt(target, parent)` to display it.
Connect `accepted` / `rejected` for the result; outside dismissal is cancellation.
It reuses Flyout positioning, shadows and animations, and is deleted on close.
The Buttons page includes a Show dialog example.

`TimeLineWidget` displays grouped timeline cards with status icons and connector
lines. Use `addGroup(title, InfoBarIcon.SUCCESS)` then `group.addItem(text, icon)`.
Cards support wrapped/rich text; groups and items can be removed dynamically.
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
| Acrylic widgets | `qfluentwidgets_pro.components.material` or `qfluentwidgets_pro.components.widgets.acrylic_label` | Optional CPU blur: NumPy, SciPy, Pillow, colorthief |
| Media playback widgets | `qfluentwidgets_pro.multimedia` | QtMultimedia / QtMultimediaWidgets |
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
charts and the CodeEdit demo. It deliberately includes Pygments for dynamic lexer
discovery and is not a minimal business-app build template. Use your own entry
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
