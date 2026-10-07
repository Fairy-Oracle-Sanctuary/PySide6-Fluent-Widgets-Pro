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
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from qfluentwidgets_pro import PushButton

app = QApplication([])
window = QWidget()
layout = QVBoxLayout(window)
layout.addWidget(PushButton("Hello, Fluent Widgets!", window))
window.resize(400, 240)
window.show()
app.exec()
```

Run `python main.py` to explore the gallery. See [gallery/README.md](gallery/README.md) for demo details.

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

`main.py` now runs the migrated free-component gallery. The **Charts** sidebar
button opens the retained, independent chart window on demand; closing and
reopening it reuses the same window. The **Chat** entry immediately below Charts
opens a native chat demo window, preserving its conversation on reopen and
stopping local simulated output on close. All 91 restored/extended components
are integrated into the matching category pages by `gallery/view/pro_examples.py`.
Interactive examples live in `gallery/pro_demos/`; the retained test fixtures
are not runtime dependencies. Heavy CodeEdit/audio demos load only when requested.

`deploy.py` builds this gallery and includes its lazy chart package; Nuitka's
PySide6 plugin collects the WebEngine renderer and resources. CPU Acrylic blur
and SciPy remain excluded. The chat demo includes Pygments for code highlighting
and Matplotlib/NumPy for offline formulas. The optional waveform demo includes
QtMultimedia plugins and its sample WAV; its runtime imports remain lazy.
Use your own entry point for a minimal business-app build.
If you use CodeEdit, include Pygments and its dynamically loaded lexers.
Final bundle contents must be checked in Nuitka's compilation report and output;
removing a root export alone does not guarantee removal of Qt plugins or native
libraries reached through other imports. `RadialGauge` is pure QtWidgets and is
exported normally; it was an accidental omission, not a heavy dependency.

## 📁 Project Structure

- `qfluentwidgets_pro/`
  - Main package (free base + restored components)
- `main.py`
  - Free-component gallery entry point; independent Charts sidebar action
- `gallery/`
  - Migrated gallery pages and assets, plus the retained chart window
- `tests/gallery_fixtures/`
  - Standalone legacy extension demos for regression tests
- `gallery/pro_demos/`
  - Interactive extension previews used by the categorized gallery
- `docs/`
  - Documentation assets

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
