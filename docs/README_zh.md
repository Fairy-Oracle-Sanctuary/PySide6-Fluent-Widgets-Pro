<p align="center">
  <img width="18%" align="center" src="../qfluentwidgets_pro\_rc\images\logo.png" alt="logo">
</p>
  <h1 align="center">
  PySide6-Fluent-Widgets-Pro
</h1>
<p align="center">
  基于 <a href="https://github.com/zhiyiYo/PyQt-Fluent-Widgets">PyQt-Fluent-Widgets</a> 的 Fluent Design 风格组件库 
</p>

<div align="center">

[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](https://github.com/Fairy-Oracle-Sanctuary/Qt-Fluent-Widgets)
[![GPLv3](https://img.shields.io/badge/License-GPLv3-blue?color=#4ec820)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?color=#4ec820)]()
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.qt.io)

</div>

<p align="center">
<a href="README.md">English</a> | 简体中文
</p>

<p align="center">
  <img src="../docs/source/_static/Interface.png" alt="interface"/>
</p>

## 项目简介

本项目希望提供一套对开发者更友好的 PySide6 Fluent Design Widgets 组件库：

- 以免费版为基础
- 尽可能还原 Pro 版常用组件/交互
- 保持 API 易用、可读、易维护


## 当前状态

- **[范围]** 部分还原（持续更新）
- **[目标]** 优先还原高频使用的 Pro 组件
- **[兼容性]** Python 3.9+ / Windows、macOS、Linux


## 使用方式

本仓库更适合作为源码依赖使用。

### 方式 1：克隆并运行示例

```bash
git clone https://github.com/<your-name>/PySide6-Fluent-Widgets-Extend.git
python main.py
```

### 方式 2：集成到你的项目

将 `qfluentwidgets_pro` 目录复制到你的工程中（或将本仓库加入 Python Path），然后：

```python
from qfluentwidgets_pro import FluentWidget
```

依赖：

- PySide6（Qt for Python）


## 快速开始

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

运行 `python main.py` 浏览组件演示。演示程序的说明见 [gallery/README.md](../gallery/README.md)。

## 按需导入与 Nuitka 打包

部分组件刻意不在包的 `__init__.py` 中统一导出，**不是漏实现**。统一入口中的导入可能让
Nuitka 把未使用的可选依赖纳入编译图；只有业务使用相应功能时，才从具体模块导入。

| 可选功能 | 按需导入模块 | 相关依赖 |
| --- | --- | --- |
| `ChartWidget` | `qfluentwidgets_pro.components.widgets.chart_widget` | QtWebEngine、QtQuickWidgets 及相关 Qt 运行库 |
| `CodeEdit`、`CodeLanguage` | `qfluentwidgets_pro.components.widgets.code_edit` | Pygments 语言解析器 |
| `ChatWidget`、`ChatMessage` | `qfluentwidgets_pro.components.widgets.chat_widget` | 可选 Pygments / Matplotlib 公式；不使用 WebEngine |
| Acrylic 组件 | `qfluentwidgets_pro.components.material` 或 `qfluentwidgets_pro.components.widgets.acrylic_label` | 可选 CPU 模糊：NumPy、SciPy、Pillow、colorthief |
| 多媒体播放组件 | `qfluentwidgets_pro.multimedia` | QtMultimedia / QtMultimediaWidgets |
| `AudioDecoder`（仅文件波形解码） | `qfluentwidgets_pro.common.audio_decoder` | QtMultimedia 及其后端/编解码器；`AudioWaveformWidget` 不需要 |
| `FramelessWebEngineView` | `qfluentwidgets_pro.qframelesswindow.webengine` | QtWebEngineWidgets |

```python
from qfluentwidgets_pro import PushButton, RadialGauge  # 轻量组件正常导出

# 只导入业务实际使用的可选组件：
from qfluentwidgets_pro.components.widgets.code_edit import CodeEdit, CodeLanguage
from qfluentwidgets_pro.components.widgets.chart_widget import ChartWidget
```

构造函数内的延迟导入、`try/except ImportError` 只是运行时行为，不能保证 Nuitka 不打包依赖。
Standalone 模式默认跟随导入；`--nofollow-import-to` 可以排除模块，但运行时使用被排除的
功能可能报错，详见 [Nuitka 官方说明](https://nuitka.net/user-documentation/use-cases.html#standalone-program-distribution)。

**Acrylic 的间接依赖需特别注意：** 导航仍会间接导入 Acrylic 辅助类。因此在安装了可选
依赖的源码环境中，仅导入包根也可能加载 NumPy/SciPy/Pillow/colorthief。无需 CPU 模糊时，
除了排除 NumPy/SciPy，还应排除 `qfluentwidgets_pro.common.image_utils`，使用已有的无模糊
回退；导航仍可使用，只是不对图片做 CPU 模糊。这不会关闭 Windows 原生云母效果。

```text
--nofollow-import-to=qfluentwidgets_pro.common.image_utils
--nofollow-import-to=numpy
--nofollow-import-to=scipy
```

`deploy.py` 打包的是 `main.py` 的**完整 gallery**，其中显式导入了图表、CodeEdit 和
音频波形及原生 Chat 展示页，包含文件解码/播放所需的 QtMultimedia，以及公式所需的
Matplotlib / NumPy。完整 gallery 不再排除 NumPy，CPU Acrylic 模糊仍独立排除。
它为动态解析器发现而主动包含 Pygments，不是轻量业务程序的打包模板。业务程序应使用自己的
入口，避免引入 gallery；未使用 CodeEdit 时不要照搬 `--include-package=pygments`，使用时则
须包含所需的动态加载解析器。最终是否纳入 Qt 插件或原生库，需要检查 Nuitka 编译报告和
产物，不能仅凭根包没有导出就判断。`RadialGauge` 为纯 QtWidgets，已补回正常导出，属于
意外遗漏，不是重型组件。

## 目录结构

- `qfluentwidgets_pro/`
  - 主包（免费版基础 + 已还原组件）
- `main.py`
  - 示例 / 调试入口
- `docs/`
  - 文档资源


## 国际化和资源编译

组件内置文案使用英文 `tr()` 字面量。更新
`qfluentwidgets_pro/_rc/i18n/qfluentwidgets.en_US.ts` 后执行：

```powershell
py -3.9 scripts/translate_ts.py --all --jobs 4 --build
```

脚本保留现有译文并同步模板新增项，仅翻译待处理文本，每批固定 50 条。
完成后生成全部 QM，并依次编译组件库、演示程序和无边框窗口的资源模块。
每批完成后保存，可断点续跑；校验占位符和文件过滤器通配符。
仅同步、不调用 API 可用 `--all --skip-translate`；仅重新编译可用
`--compile-qm --compile-resources`。
API 密钥优先读取 `DEEPSEEK_API_KEY` 环境变量，也可放在被 Git 忽略的
`scripts/translate_ts.local.json`（`{"api_key": "..."}`），不要提交密钥。

## 免责声明

- 本项目为**社区驱动**的还原/扩展项目
- 与官方 QFluentWidgets Pro **无任何隶属关系**
- 请遵守原项目的开源协议与商业条款

## 🙏 致谢

- `Pager` `DropMultiFilesWidget` `DropSingleFileWidget` `Splitter` `PinBox` `LabelLineEdit` `Toast` 组件实现参考了 [PySide6-Fluent-UI](https://github.com/HiyorinI/PySide6-Fluent-UI) (作者 HiyorinI)


## 计划（Roadmap）

- 统一组件 API 与文档
- 持续还原更多 Pro 组件（按社区需求优先级）
- 补充更多示例与截图
