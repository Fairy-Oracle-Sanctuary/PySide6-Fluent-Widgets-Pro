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
  <img src="../docs/source/_static/Interface_en.png" alt="interface"/>
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


## 已还原组件

已还原或扩展的组件共 61 个（列表将持续更新）：

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

        self.progressButton = IndeterminateProgressPushButton("下载中...", self)
        layout.addWidget(self.progressButton)


app = QApplication([])
w = Window()
w.show()
app.exec()
```

`IndeterminateProgressPushButton` 会跟随当前主题和自定义主题色。
加载动画默认自动播放，可通过 `start()` / `stop()` 控制，使用 `isSpinning()` 查询状态。
点击按钮会正常发出 `clicked` 信号，不会切换动画状态。

`ProgressPushButton` 常态与主题色按钮一致，进度态显示居中的进度环和停止图标。
使用 `setProgressing(True)` 切换形态、`setValue(0..100)` 更新进度。
`setAutoProgressEnabled(True)` 开启点击进入进度态（默认关闭）；进度态点击发出
`stopRequested`，由业务处理取消。达到 100 不会自动切换形态。Buttons 页面提供模拟下载。

`ImageComparisonSlider(before, after)` 通过可拖动竖线和半透明双向箭头手柄对比两张图片。
支持路径、QImage、QPixmap；`setImages()` 更换图片，`setValue(0..100)` 设置分割百分比，
`valueChanged` 通知变化。支持方向键及 Home/End，Magnifier 页面提供双图对比示例。

`AvatarPicker` 继承 AvatarWidget，悬停显示暗色圆形遮罩和白色相机图标，
点击选图后复用 ImageCropper 的圆形裁剪；确认更新头像并发出 `imageChanged(QImage)`，
取消保留原头像。通过 `setRadius()` 调整大小，`cropImage(image)` 直接打开指定图片裁剪。
Magnifier 页面包含头像选择器示例。

`ImageCropper(image, parent)` 提供四角缩放、区域拖动、旋转和水平翻转。
确认时通过 `imageCropped` 返回 QImage，取消保留调用方原预览。
`setCropShape(CropShape.CIRCLE)` 启用圆形裁剪，`setCropPathFactory(factory)`
扩展自定义 QPainterPath 形状；工具栏形状按钮按官方展示保持禁用。
展示页通过“选择图像”打开裁剪并更新预览，不提供保存/导出按钮。

`ImageMagnifierWidget` 继承 ImageLabel，悬停时显示跟随鼠标的圆形放大镜，
带主题色边框和十字标记。通过 `setMagnification(2.0)` 调整倍率、`setRadius(50)`
调整镜片半径，`setMagnifierEnabled(False)` 关闭。支持原有图片/缩放接口，
聚焦后可用方向键移动镜片；Magnifier 展示页提供 2×、3×、4× 切换。

`FlyoutDialog` 提供自定义内容区域和底部确认/取消图标按钮。
通过 `addWidget()` 添加控件、`showAt(target, parent)` 弹出，连接 `accepted` / `rejected`
处理结果；点击外部关闭按取消处理。复用 Flyout 的定位、阴影和动画，关闭后自动删除。
Buttons 页面提供 Show dialog 示例。

`TimeLineWidget` 提供分组标题、状态图标、连接线和圆角条目卡片。
通过 `addGroup(title, InfoBarIcon.SUCCESS)` 创建分组，再调用 `group.addItem(text, icon)`
添加条目；支持富文本、自动换行、动态移除分组和条目。TimeLine 展示页包含已完成、今日安排和待办事项。

`FilledFluentWindow` 提供默认展开的侧边栏、主题色填充的选中项和搜索框。
沿用 `FluentWindow` 的 `addSubInterface()` / `switchTo()` 接口，
搜索框自动搜索已注册页面的导航名称，点击结果或使用方向键和回车跳转。
按 Esc 关闭结果列表，清空输入不会改变当前页面；页面增删会同步更新搜索结果。
运行 `main.py`，在主页点击“打开 FilledFluentWindow 窗口”，
即可体验页面切换、搜索，以及设置页中的主题和自定义主题色切换。


## 目录结构

- `qfluentwidgets_pro/`
  - 主包（免费版基础 + 已还原组件）
- `main.py`
  - 示例 / 调试入口
- `docs/`
  - 文档资源


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
