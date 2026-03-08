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
  <img src="docs/source/_static/Interface_en.png" alt="interface"/>
</p>

## 📌 Introduction

This repository is based on the **free version** of QFluentWidgets (PySide6 port) and aims to **restore / re-implement some components and behaviors from the Pro version**.

Only a subset has been restored so far. The goal is to provide a drop-in, developer-friendly widget library for PySide6 with a Fluent Design look & feel.

## ✨ Status

- **[scope]** Partial restoration (work in progress)
- **[target]** Restore commonly used Pro widgets/components first
- **[compatibility]** Python 3.9+ / Windows, macOS, Linux

## 🧩 Restored Components (partial)

The following components have been restored or extended in this repo (the list will be updated continuously):

`HyperlinkToolButton` `FilledPushButton` `FilledToolButton`
`TextPushButton` `TextToolButton` `LuminaPushButton`
`OutlinedPushButton` `OutlinedToolButton` `RoundPushButton`
`RoundToolButton` `Chip` `Tag` `SubtitleCheckBox`
`SubtitleRadioButton` `ToolTipSlider` `RangeSlider`
`Pager` `FilledProgressBar` `MultiSegmentProgressRing`
`RadialGauge` `DropMultiFilesWidget` `DropSingleFileWidget`

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
from qfluentwidgets_pro import FluentWidget, FluentIcon, ToolTipSlider, RangeSlider, HyperlinkToolButton


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


app = QApplication([])
w = Window()
w.show()
app.exec()
```

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

## � Acknowledgments

- `Pager` `DropMultiFilesWidget` `DropSingleFileWidget` component implementation references [PySide6-Fluent-UI](https://github.com/HiyorinI/PySide6-Fluent-UI) by HiyorinI

## �🗺️ Roadmap

- Improve widget API consistency and documentation
- Restore more Pro widgets/components (prioritized by community needs)
- Add more examples and screenshots

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 🏆 Contributors

<a href="https://github.com/Fairy-Oracle-Sanctuary/PySide6-Fluent-Widgets-Pro/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Fairy-Oracle-Sanctuary/PySide6-Fluent-Widgets-Pro&v=2" />
</a>