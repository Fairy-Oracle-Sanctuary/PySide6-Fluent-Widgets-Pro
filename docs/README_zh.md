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


## 已还原组件

已还原或扩展的组件共 82 个（列表将持续更新）：

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
    FluentWidget,
    FluentIcon,
    ToolTipSlider,
    RangeSlider,
    HyperlinkToolButton,
    IndeterminateProgressPushButton,
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

`Toast.success(title, content, parent=window)` 显示顶部绿色状态条、标题、正文和可选关闭按钮。
同时支持 `info`、`warning`、`error`；`duration=-1` 持续显示直到手动关闭。
`ToastPosition` 提供六种位置，不同窗口分别堆叠，主页 Success 按钮展示 Lesson 4 示例。

`ProgressInfoBar` 复用 InfoBar 的定位、堆叠、中性背景和关闭按钮，环的运动直接沿用
不确定进度环。默认持续显示，关闭通知不会自动取消业务任务。主页提供演示按钮。

```python
from qfluentwidgets_pro import ProgressInfoBar

bar = ProgressInfoBar.new("请勿离开", "正在发送邮件，请耐心等待...", parent=window)
bar.setContent("正在上传附件...")
bar.setRemainingTime("剩余 10 秒")  # 可选文本，由业务计算、格式化
bar.setValue(65)  # 切换为确定进度，范围 0..100
bar.setIndeterminate(True)  # 切回不确定进度环
bar.close()  # 任务结束后关闭
```

支持 `setTitle()`、`setCustomBarColor(light, dark)`；剩余时间传空字符串可移除。
位置使用 `InfoBarPosition`，`duration=-1` 持续显示；提供 `closedSignal` 和 `valueChanged`。

`ProgressToast` 以紧凑的单行通知显示状态图标、提示信息、关闭按钮和底部进度条，带阴影。
复用 Toast 的定位和堆叠；`info`、`warning`、`error` 默认进度为 0，`success` 为 100。
默认持续显示，进度达到 100 不会自动切换状态、文案或关闭通知。

```python
from qfluentwidgets_pro import ProgressToast, InfoBarIcon

toast = ProgressToast.warning("正在下载文件，请耐心等待...", value=77, parent=window)
toast.setStateColor(InfoBarIcon.WARNING, "#9D5D00", "#FCE100")
toast.setStateColor(InfoBarIcon.SUCCESS, "#0F7B0F", "#6CCB5F")
toast.setValue(100)
toast.setIcon(InfoBarIcon.SUCCESS)
toast.setContent("文件下载成功")
```

两种状态颜色都可自定义，状态图标与进度条同步使用配置颜色。
`setStateColor(状态, 浅色, 深色=None)` 分别配置状态；`setCustomBarColor(浅色, 深色=None)`
为没有单独配置的状态提供统一颜色。不传深色则两个主题使用同一颜色。
`setUseAni(False)` 可禁用数值过渡；支持 `ToastPosition`、`duration`、`isClosable`、
`closed` 和 `valueChanged`。关闭通知不会自动取消任务，主页提供模拟下载和完成状态示例。

`RoundProgressToast` 是胶囊形加载通知，显示不确定进度环和提示文字，不含关闭按钮或状态条。
环的运动复用 `IndeterminateProgressRing`，颜色跟随当前主题色，隐藏时暂停。
复用 Toast 的位置、堆叠和 `closed` 信号。

```python
from qfluentwidgets_pro import RoundProgressToast

toast = RoundProgressToast.new("加载中，请稍候", parent=window)
toast.setContent("正在处理...")
toast.close()  # 任务结束后关闭
```

默认 `duration=-1` 持续显示，传入非负毫秒数可自动关闭；主页演示显示五秒的加载通知。

`RatingWidget(4.5)` 显示数值和右侧橙色矢量星标，通过 `setValue(数值)` 更新评分，
`valueChanged(float)` 通知变化。只展示评分，不提供点击星星打分的交互，也不限制为五分制。
`setDecimals(0..6)` 控制显示精度（默认一位小数，省略末尾零），
`setStarColor(浅色, 深色=None)` 可自定义星标颜色。主页提供数值输入框测试评分变化。

`InteractiveRatingWidget(3)` 显示五颗橙色星星：悬停时填满前面的星星，并按鼠标精确 X
坐标裁切当前星星，不取整、不限制半星。点击确认评分，移出恢复已确认的评分。
`setValue(0..5)` 设置评分，`hovered(float)` 通知预览，`valueChanged(float)` 通知确认值变化，
`displayValue()` 返回当前展示的评分。`setReadOnly(True)` 禁止修改；方向键按 0.1 调整，
Home/End 设置为 0/5。复用 `setStarColor(浅色, 深色=None)`，主页提供悬停和点击演示。

`RoundTabWidget` 提供与 `QTabWidget` 类似的常用页面管理接口，内部使用 `RoundTabBar`，
选中标签与下方圆角内容框统一绘制轮廓，避免弧线接头出现缝隙或描边叠加。
页面内容由使用者自己创建并传入。

```python
from PySide6.QtWidgets import QWidget
from qfluentwidgets_pro import RoundTabWidget, FluentIcon

tabs = RoundTabWidget(window)
tabs.addTab(QWidget(), '歌曲')
tabs.addTab(QWidget(), FluentIcon.FOLDER, '专辑')
tabs.setCurrentIndex(1)
tabs.currentChanged.connect(on_page_changed)
tabs.tabCloseRequested.connect(tabs.removeTab)
tabs.tabAddRequested.connect(add_page)
```

支持 `addTab(页面, 标题)` / `addTab(页面, 图标, 标题)` 与对应的 `insertTab()` 重载，
以及 `widget()` / `indexOf()` / `currentWidget()`、切换页面、文本／图标／提示、
启用／禁用、显示／隐藏、`clear()`、关闭按钮、拖拽和 `setTabBarAutoHide()`。
也兼容原 `TabWidget` 的 `(页面, 标题, 图标, routeKey)` 参数顺序。
`tabBar()` 返回内部圆角标签栏，同时保留原库的 `tabBar` 属性访问方式。
Ctrl+Tab / Ctrl+Shift+Tab 可循环切换可见且启用的标签。添加／关闭信号只发出请求；
`removeTab()` / `clear()` 不会销毁页面，需要释放时自行调用 `deleteLater()`。
容器会自动同步页码、选中状态和拖拽后的页面顺序，程序切换也会通知 `currentChanged`。
`setTabSelectedBackgroundColor(浅色, 深色)` 会同时更新内容背景。
这是顶部圆角样式的页面容器，不是 `QTabWidget` 子类，不提供 Qt 的其他标签方位／形状
及原生角落控件接口。组件为轻量实现，已从包根目录导出，按钮页提供完整示例。

`RoundTabBar` 是已有 `TabBar` 的样式变体：上方圆角、底部两侧向外衔接的弧线，
选中标签绘制 1px 顶部／侧边描边，不画底边，默认关闭标签阴影。底部外扩采用 5px 四分之一圆弧，
相邻标签共享 5px 弧线区域，让标签紧贴而不压缩圆角；悬停背景延伸到标签边缘。
标签栏高 38 逻辑像素，标签高 32px、上方圆角 8px，
默认最大标签宽度为 200px。标签栏背景保持透明，由应用控制其所在区域的底色。
`main.py` 为演示区域设置浅灰背景，让浅色选中标签清晰可辨，不在组件内写死背景。
普通 `TabBar` 的外观和交互不变。

```python
from qfluentwidgets_pro import RoundTabBar, FluentIcon, TabCloseButtonDisplayMode

bar = RoundTabBar(window)
bar.addTab('songs', '歌曲', FluentIcon.MUSIC)
bar.addTab('albums', '专辑', FluentIcon.FOLDER)
bar.setCurrentTab('albums')
bar.setMovable(True)
bar.setScrollable(True)
bar.setTabMaximumWidth(200)
bar.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.ON_HOVER)
bar.tabCloseRequested.connect(close_page)
bar.tabAddRequested.connect(add_page)
bar.currentChanged.connect(switch_page)
```

添加／关闭按钮只发出请求，由应用维护页面并调用 `addTab()` / `removeTab()`。
继承路由键、插入、数据、图标／文本、显示／隐藏、启用／禁用、拖拽排序及 `tabMoved`，
关闭按钮支持始终显示／悬停显示／不显示。与原 `TabBar` 一致，程序调用
`setCurrentTab()` / `setCurrentIndex()` 不发出 `currentChanged`，需同时更新自己的页面容器。
想与下方内容无缝衔接，使用上下间距为 0 的布局，并通过
`setTabSelectedBackgroundColor(浅色, 深色)` 让选中背景与内容背景一致。
按钮页示例提供动态页面和可拖拽、可滚动、最大宽度、关闭按钮模式四个设置项。
组件为轻量实现，已从包根目录导出。

`GuideWindow` 直接继承项目内 `qframelesswindow.FramelessWindow`，通过 `show()` 显示为
独立、非模态窗口，在 Windows 任务栏可见。Windows 11 默认通过原有 `windowEffect` 启用原生云母，
`setMicaEffectEnabled(False)` 可切回纯色主题背景，不支持云母的系统自动使用纯色背景。
只提供可拖动且仅保留关闭按钮的标题栏、
页面容器、现有 `PipsPager` 和上一步／下一步／完成导航，里面的内容由使用者自行提供。
默认 670×460 逻辑像素，底栏高 80px；图片、表单、校验提示及保存逻辑都不写死。

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets_pro import GuideWindow, LineEdit

guide = GuideWindow(parent=window)  # 仅用于居中和生命周期关联，不设置系统 owner。
page = QWidget()
page_layout = QVBoxLayout(page)
name_edit = LineEdit(page)
page_layout.addWidget(name_edit)
guide.addPage(page)
guide.addPage(QWidget())
guide.finished.connect(save_settings)
guide.cancelled.connect(on_cancel)
guide.show()  # 应用应保留 guide 的 Python 引用。
```

`addPage(page)` / `insertPage(index, page)` 返回页面索引，`removePage(page)` 隐藏并移出页面但不删除。
通过 `count()`、`page(index)`、`currentPage()`、`currentIndex()` 和 `setCurrentIndex(index)`
管理任意页面，`currentIndexChanged(int)` 通知步骤变化。圆点与上一步／下一步同步，末页显示“完成”。
可覆写 `validatePage(page)`，返回 False 阻止前进或完成；`setNextEnabled(False)` 同样阻止向前点击圆点。
返回上一步不做校验；`setCurrentIndex()` 则是应用主动切换，不经过校验。
`setStepNavigationEnabled(False)` 禁止点击圆点和通过圆点键盘导航，适合必须逐步填写的场景。
成功完成发出 `finished()` 并关闭；Esc 或关闭按钮发出 `cancelled()`，不会误触完成逻辑。
重新打开保留页面和填写内容，需重新开始时调用 `setCurrentIndex(0)`；`moveToCenter()` 在父窗口／屏幕居中。
可选 `parent` 不会设为 Qt／系统窗口父对象，避免带 owner 的窗口不显示在任务栏；
关闭向导不会关闭参考窗口。任务栏是否合并为同一应用分组仍遵循系统设置。
组件为轻量实现，已从包根目录导出。按钮页提供三步示例，示例页面自行构建，不保存令牌、不联网。

`MenuBar` 复用现有 `RoundMenu` 提供顶部菜单导航，标题高 32 逻辑像素。
点击标题打开，菜单打开后移到其他标题直接切换；再次点击同一标题、点击弹窗外部
或按 Esc 关闭。Alt+助记字母（如 `&F`）或 F10 可用键盘导航，支持方向键、
Home/End、Enter，以及分隔线、禁用项、勾选项和子菜单。

```python
from PySide6.QtGui import QAction
from qfluentwidgets_pro import MenuBar

bar = MenuBar(window)
file_menu = bar.addMenu('文件(&F)')  # 也可传入已有的顶级 RoundMenu。
open_action = QAction('打开文件...', window, shortcut='Ctrl+O')
file_menu.addAction(open_action)
file_menu.addSeparator()
file_menu.addAction(QAction('新建文件...', window))
bar.triggered.connect(handle_action)  # 收到触发的 QAction。
layout.addWidget(bar)
```

菜单中的 QAction 快捷键仅在当前窗口内、菜单归属可见且启用的菜单栏时注册，
不是系统全局快捷键；隐藏或禁用菜单标题不会触发其快捷键。
`insertMenu(before, menu)`、`removeMenu(menu)` 和 `clear()` 管理菜单且不删除可复用菜单；
`setActiveMenu(menu)` 打开，`setActiveMenu(None)` / `closeActiveMenu()` 关闭，
`activeMenuChanged(menu或None)` 通知切换。也支持 QWidget 自带的 action 方法添加直接执行的标题。
组件为轻量 Qt 实现，可从包根目录导入；演示位于按钮页顶部。

`WaitingDialog` 显示居中的等待面板和窗口模态遮罩，包含跟随主题色的
`IndeterminateProgressRing`、标题和说明，不带底部按钮，按 Esc 取消。
标准面板为 300×132 逻辑像素，进度环为 56px；较长文字会自动换行并增加面板高度。

```python
from qfluentwidgets_pro import WaitingDialog

dialog = WaitingDialog('请耐心等待...', '正在准备下载任务中 ...', parent=window)
dialog.rejected.connect(cancel_task)  # 如需同时取消实际后台任务，由应用显式连接。
dialog.open()  # 非阻塞显示，任务期间保留 dialog 引用。
# 通过后台线程信号在 GUI 线程更新：
# worker.statusChanged.connect(dialog.setContent)
# worker.finished.connect(dialog.accept)
```

支持 `setTitle()` / `setContent()` 动态更新、`title()` / `content()` 获取文字。
`accept()` 表示完成，`reject()` / Esc 表示取消，连接 `accepted`、`rejected` 或
`finished(int)` 处理结果。Esc 只关闭对话框，不会自行终止任务；如需取消任务须显式连接。
耗时工作应在后台线程进行，否则主线程被阻塞时进度环和 Esc 都无法响应。
关闭开始即停止动画，复用同一对象再次打开会重新启动；要求传入父窗口，遮罩跟随父窗口
移动/缩放，父窗口隐藏时关闭。默认点击遮罩不退出。轻量纯 QtWidgets，正常从主包导出，
Buttons 示例页提供等待对话框入口。

`ShortcutPicker` 复用可点击的 `CardWidget`，显示跟随主题色的独立键帽。
整个卡片（包括键帽、间隙和铅笔图标）都可点击，打开带遮罩的快捷键捕获对话框；
聚焦后也可按 Enter / Space 打开。悬停、按下效果复用卡片背景动画。
按键只更新草稿，点击保存才生效；重置恢复配置的默认组合键，取消不修改原快捷键。

```python
from PySide6.QtGui import QKeySequence, QShortcut
from qfluentwidgets_pro import ShortcutPicker

picker = ShortcutPicker('Ctrl+Shift+A', parent=window)
picker.setDefaultKeySequence('Ctrl+Shift+A')
picker.setDialogTitle('激活快捷键')
picker.setDialogDescription('按下组合键以更改此快捷键')
picker.keySequenceChanged.connect(lambda seq: print(seq.toString(QKeySequence.PortableText)))
# 组件只负责捕获；需要触发业务操作时由应用自行注册：
shortcut = QShortcut(picker.keySequence(), window)
picker.keySequenceChanged.connect(shortcut.setKey)
shortcut.activated.connect(your_action)
```

`keySequence()` / `defaultKeySequence()` 返回副本；`setKeySequence()` 接受 QKeySequence、
QKeyCombination、Qt 按键或 PortableText 字符串，仅支持一个组合键，不支持多段连续序列；
无效输入会报错，原状态不变。`clear()` 清空，`reset()` 立即恢复默认值。
`keySequenceChanged(QKeySequence)` 通知实际变化；每次保存都会发出
`keySequenceSelected(QKeySequence)` 和 `editingFinished()`，包括保存未变更的值；
取消发出 `editingCanceled()`。支持 `showEditor()` / `cancelEditing()` 和 `isEditing()`。

支持 Ctrl / Alt / Shift / Meta 单键与组合、功能键和小键盘。默认 Esc 取消，
`setEscapeCancelsCapture(False)` 后可录制 Esc，此时需点击取消按钮退出。
Enter、Space、Tab 均作为待录制按键，不会误触保存或切换焦点。录制期间拦截应用内快捷键，
关闭后恢复正常；不安装系统全局键盘钩子，系统保留的组合键可能无法捕获，纯修饰键能否
注册为有效快捷键也取决于 Qt 和操作系统。轻量纯 QtWidgets，正常从主包导出。
Buttons 示例页提供中文对话框、清空按钮及保存后触发快捷键的测试。

`CircleColorPicker` 用于从自定义圆形色板中选择一个颜色。选中态为同色细外环，
外环与色块之间保留透明间隙；组件背景透明，浅色和深色主题下均保留色板原色。
它不绑定也不修改应用主题色，`colorChanged(QColor)` 只通知选中的颜色。

```python
from qfluentwidgets_pro import CircleColorPicker

picker = CircleColorPicker(['#FF4343', '#FFB900', '#107C10'])
picker.setColor('#FFB900')
picker.colorChanged.connect(lambda color: print(color.name()))
```

`setColors(iterable)` 替换色板，`addColor()` / `addColors()` 追加颜色，`colors()` 返回副本。
`setColor()` 选择色板里已有的颜色，`setCurrentIndex()` 按序号选择，传 `-1` 清除选中；
`color()`、`currentIndex()`、`count()` 获取状态，未选中或空色板时返回无效 QColor。
替换色板时尽量保留原选中颜色，否则选中第一项；允许重复颜色，不同色块之间切换
会发出 `currentIndexChanged(int)`，颜色相同则不重复发出颜色变化信号。
方向键和 Home/End 切换，空格/Enter 选择。Colors 示例页可编辑并应用自定义色板，
不会把选中的颜色设置为主题色。组件为纯 QtWidgets，可在主包导出，无需重型依赖。

`DropDownColorPicker` 为带确认/取消的下拉颜色编辑器，包含色相/饱和度面板、亮度条、
RGB / HSV 切换、十六进制输入、RGBA / HSVA 数值及彩色渐变滑条。按钮 QSS、Flyout、
输入控件和滑条动画手柄均复用现有实现，渐变只通过 Qt 绘制。

```python
from qfluentwidgets_pro import DropDownColorPicker

picker = DropDownColorPicker('#0078D4', parent=window)
picker.colorChanged.connect(lambda color: print(color.name(color.HexArgb)))
picker.setAlphaEnabled(True)  # 默认开启透明度编辑
```

`setColor()` / `color()` 设置或读取已确认的 8 位 QColor 副本。拖动或输入只修改草稿，
发出 `colorPreviewed(QColor)`，不会直接改变按钮已确认颜色。勾号提交，颜色实际变化
才发出 `colorChanged(QColor)`，每次确认均发出 `colorSelected(QColor)`；叉号、Esc 或
点击外部放弃草稿，发出 `pickingCanceled()`。`showPicker()` / `closePicker()` 控制浮层。
十六进制支持 `#AARRGGBB` 和 `#RRGGBB`，6 位输入保留当前透明度；RGB 和透明度为
0–255，HSV 为色相 0–359、饱和度/亮度 0–100。灰度或亮度为零时保留色相，恢复数值
后不会意外跳到红色。无效或未完成输入不会写入无效颜色。`isAlphaEnabled()` 查询设置；
关闭透明度编辑会取消当前草稿、隐藏 A 行，并将已确认颜色转为不透明。
较小屏幕上编辑区可滚动，底部确认/取消始终可见。选色不绑定也不修改应用主题色。
组件正常从主包导出，无 Pillow、NumPy、QtMultimedia 等重型依赖，Colors 示例页可体验。

`DropDownColorPalette` 为复用按钮 QSS 的下拉调色盘，包含 Automatic（自动颜色）、
6 排 × 10 列主题色、10 个标准色和 More Colors。面板复用现有 Flyout，点击外部
或按 Esc 收起，不改变原颜色。More Colors 先收起色板，再打开现有
[ColorDialog](https://pyqt-fluent-widgets.readthedocs.io/zh-cn/latest/autoapi/qfluentwidgets/components/dialog_box/color_dialog/index.html)，
只在确认后提交颜色，取消保持原色。

```python
from qfluentwidgets_pro import DropDownColorPalette

picker = DropDownColorPalette('#0078D4', parent=window)
picker.colorChanged.connect(lambda color: print(color.name()))
picker.setAutomaticColor('#000000')
picker.setAlphaEnabled(True)  # 可选：更多颜色对话框显示透明度编辑
```

`setColor()` / `color()` 设置颜色或读取 QColor 副本；`colorChanged(QColor)` 仅通知
实际变化，`colorSelected(QColor)` 通知每次用户确认（包含相同颜色）。`setAutomatic()`
选择明确的自动颜色，`automaticColor()`、`isAutomatic()` 和 `automaticChanged(bool)`
查询颜色或模式。自动颜色默认黑色，不随应用主题色或明暗主题变化。
`showPalette()` / `closePalette()` 控制面板，`showColorDialog()` 打开更多颜色；
`isAlphaEnabled()` 查询透明度设置，默认关闭。方向键和 Home/End 移动色块焦点，
空格/Enter 确认。主题色只是预设色板，不绑定也不修改应用主题色；无效颜色会被拒绝，
原状态保持不变。组件为轻量 QtWidgets，正常从主包导出，Colors 示例页可直接体验。

`ScreenColorPicker` 为“当前颜色块 + 滴管”按钮。点击或调用 `startPicking()` 后，
鼠标旁显示颜色块与十六进制值预览；左键或 Enter/空格确认，Esc 或右键取消，
取消不改变原颜色。它只选取颜色，不绑定也不修改应用主题色。

```python
from qfluentwidgets_pro import ScreenColorPicker

picker = ScreenColorPicker('#0078D4')
picker.setFreezeScreenEnabled(False)  # Windows 实时取色；True 冻结画面
picker.colorChanged.connect(lambda color: print(color.name()))
```

`setColor()` / `color()` 设置或读取已确认 QColor；`colorChanged(QColor)` 通知实际变化，
`colorPicked(QColor)` 通知每次确认（包括相同颜色），`colorHovered(QColor)` 只通知预览。
`isPicking()`、`pickingChanged(bool)`、`cancelPicking()`、`pickingCanceled()` 控制或监听取色状态。
按钮继承 PushButton，常态/悬停/按下/禁用的背景和边框全部复用按钮 QSS，高度为标准 32px。
`setFreezeScreenEnabled(True/False)` 设置冻结/实时取色，`isFreezeScreenEnabled()` 查询，
默认开启冻结。取色中改变设置会取消当前会话，保留已确认颜色，下次开始使用新模式。
冻结模式在浮层显示前一次性截图；实时模式使用透明浮层，不显示旧截图，以约 30Hz
重新采样鼠标下方的像素，鼠标不移动也会更新，确认时再次采样当前颜色。
实时浮层及预览卡片通过 Windows 窗口显示亲和性排除在截图外，避免污染采样；
要求 Windows 10 2004 及以上与原生 Qt Windows 后端。不支持的平台或排除失败会提示错误，
不会偷偷改为冻结或返回浮层颜色；仅开始实时取色时才加载标准库 ctypes，不引入重型依赖。
Windows 排除截图机制见
[SetWindowDisplayAffinity 文档](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity)。
各屏幕独立处理，坐标按截图尺寸映射，支持负坐标副屏和不同 DPI。
截图不写入文件，结束立即释放。隐藏/禁用控件、应用失去激活或屏幕布局变化会取消；
同一时间只能有一个取色会话。截图不可用时发出 `errorOccurred(str)`，保留原颜色。
系统屏幕录制权限及平台限制仍然适用，受保护内容可能为空，Wayland 下 Qt 截图可能不可用。
Colors 示例页提供冻结勾选项与错误提示。组件使用 QtGui/QtWidgets，正常从主包导出，
不引入 Pillow、NumPy 或 QtMultimedia。截图与高 DPI 说明见
[QScreen::grabWindow 文档](https://doc.qt.io/qt-6/qscreen.html#grabWindow)。

`CodeEdit` 基于原生 QPlainTextEdit，支持行号、当前行底色、缩进和 20 种语言高亮。
使用前安装可选依赖（库的其他控件不需要此依赖）：

```bash
python -m pip install -r requirements-codeedit.txt
```

```python
from qfluentwidgets_pro.components.widgets.code_edit import CodeEdit, CodeLanguage

editor = CodeEdit(language=CodeLanguage.JSON)
editor.setPlainText('{"enabled": true}')
editor.setLanguage("python")  # 只切换高亮，不修改代码
editor.setIndentSize(4)
editor.setLineNumbersVisible(True)
```

内置 Python、C、C++、C#、Java、JavaScript、TypeScript、JSON、HTML、CSS、XML、
YAML、TOML、INI、Bash、PowerShell、SQL、Go、Rust、Markdown。
后台使用 Pygments 对全文进行词法分析，保留多行和内嵌语言语义；丢弃过期版本，
仅对格式变化的行分批应用 Qt 高亮。超过 100 万字符时保留编辑、停用高亮，
通过 `highlightingFailed` 通知限制或词法错误。首版不包含自动补全、折叠、诊断或文件保存。
CodeEdit 展示页支持语言选择、加载示例、只读/行号开关和主题切换。

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

`RangeCalendarPicker` 复用 CalendarPicker 的滚动日历；`FastRangeCalendarPicker`
复用 FastCalendarPicker 的轻量分页日历，并支持 `setFlyoutAnimationType()`。
第一次点击起点，移动鼠标预览，第二次点击终点提交。起止日期显示主题色描边，
范围内铺设跨周行连接的中性底色。支持反向排序、同日及跨月/年范围；
Esc 或外部点击取消未完成选择，保留已提交的范围。`setResetEnabled(True)` 显示重置按钮。

```python
from PySide6.QtCore import QDate
from qfluentwidgets_pro import RangeCalendarPicker, FastRangeCalendarPicker

picker = FastRangeCalendarPicker()
picker.setDateRange(QDate(2024, 3, 13), QDate(2024, 3, 21))
picker.setDateFormat('yyyy-MM-dd')
picker.rangeChanged.connect(lambda start, end: print(start, end))
start, end = picker.dateRange()  # 也可读取只读属性 startDate / endDate
```

`reset()` 清空已有选择时发出两个无效 QDate；`setDate(date)` 设置同日范围。
Buttons 展示页同时提供普通版和 Fast 版示例，两者均为纯 Qt 组件并在主包导出。
默认允许选择所有星期。在打开日历前调用 `setDisabledWeekDays({6, 7})` 可禁用周末
（周一=1，周日=7）：禁用日期显示灰色删除线，不能作为端点，但可处于范围内部。
修改配置后，如果现有范围端点被禁用，会清空该范围。示例开启周末禁用，并默认隐藏重置按钮。

`CalendarTimePicker` 将现有滚动日历和 24 小时时间滚轮组合在一个弹层中；
`FastCalendarTimePicker` 改用 Fast 分页日历。底部共用确认/取消按钮，日期和时间
一起提交。点击日期或滚动时间只修改草稿；取消、Esc、点击外部均保留原值，
Enter 确认。两者均为轻量 Qt 组件，在主包导出。

```python
from PySide6.QtCore import QDate, QDateTime, QTime
from qfluentwidgets_pro import CalendarTimePicker, FastCalendarTimePicker

picker = FastCalendarTimePicker()
picker.setDateTime(QDateTime(QDate(2026, 2, 10), QTime(20, 0, 0)))
picker.setDateTimeFormat('yyyy-MM-dd HH:mm:ss')
picker.dateTimeChanged.connect(lambda value: print(value))
value = picker.dateTime  # QDateTime 副本；也可读写 date / time 属性
```

默认显示秒。`setSecondVisible(False)` 隐藏秒列并将默认格式切换为分钟，
此模式确认后秒为 0；自定义格式不会被覆盖。`setDate()` / `setTime()` 保留另一部分，
支持零点时间，并在编辑时保留原 QDateTime 的时区信息。
`setResetEnabled(True)` 显示日历重置按钮；`reset()` 清空选择并发出无效 QDateTime。
仅日期或时间发生变化时，才发出对应的 `dateChanged` / `timeChanged`。
两个版本均支持 `setFlyoutAnimationType()`，Buttons 展示页已加入示例。

`AudioWaveformWidget` 是透明背景的纯 QtWidgets 波形组件，正常在主包导出。
不导入 QtMultimedia、NumPy 或解码类，也不负责播放声音。用圆头细竖线展示每个
时间区间的最小/最大振幅，静音显示为中心小点；已播放/未播放颜色分别支持浅深主题。
缓存采样块极值和可见线条，进度变化不重新扫描 PCM。

```python
from qfluentwidgets_pro import AudioWaveformWidget

waveform = AudioWaveformWidget()
waveform.setSamples(samples, sampleRate=24000)  # 归一化单声道数值，范围 -1..1
waveform.appendSamples(chunk, sampleRate=24000)  # 也可分块追加 TTS 数据
player.positionChanged.connect(waveform.setPosition)  # 毫秒
waveform.seekRequested.connect(player.setPosition)
```

`setSamples()` 重置播放位置；`appendSamples()` 保留绝对播放位置和振幅尺度，
横向适配当前已收到的数据长度。同一流采样率必须一致，切换前调用 `clear()`。
拒绝 NaN/Infinity，超出范围的有限数值会裁剪；输入数据会复制保存。
所有控件接口应在 GUI 线程调用，后台生产数据时使用排队信号。
可配置 `setBarWidth()`、`setBarSpacing()`、`setAmplitudeScale()`、
`setWaveformColor(light, dark)` 和 `setPlayedColor(light, dark)`。
点击/拖动、左右方向键（1 秒）、Home/End 发出跳转请求；
`setSeekEnabled(False)` 关闭交互。`duration()` / `position()` 均以毫秒计。
Waveform 展示页可自行选择本地音频文件，增量解码波形，并支持实际播放、暂停、停止
及波形跳转。展示页显式导入可选解码类和 QtMultimedia 播放器，波形 Widget 自身
的导入链仍不包含这些依赖。“加载测试 WAV”使用
`gallery/resource/audio/waveform_sample.wav`：5 秒、24 kHz、单声道、16 位 PCM
合成测试音，不是人声录音。如需另存一份，可运行
`python examples/audio_waveform/generate_sample.py --output test.wav`，不会覆盖已有文件。
Windows 下 `main.py` 在原生多媒体插件可用时默认采用 Windows 后端，避开本机复现的
FFmpeg 输出声道布局错误；显式设置的 `QT_MEDIA_BACKEND` 会被保留。
库本身不选择或修改后端，可用格式仍由所选后端决定。gallery 打包脚本已包含
多媒体插件及测试 WAV 数据文件。

`AudioDecoder` 单独作为**重型可选辅助类**，不在任何 `__init__.py` 导出。
需要读取音频文件时，必须从具体模块显式导入：

```python
from qfluentwidgets_pro.common.audio_decoder import AudioDecoder

decoder = AudioDecoder(parent=waveform)  # 解码期间需保留对象
decoder.decoded.connect(waveform.setSamples)
decoder.errorOccurred.connect(print)
decoder.decode('speech.wav')
# 需要增量显示时：每次 decode 前清空波形，改为连接
# decoder.samplesReady 到 waveform.appendSamples，不再连接 decoded。
```

通过 Qt 的 [QAudioDecoder](https://doc.qt.io/qt-6/qaudiodecoder.html) 异步解码，
将 UInt8/Int16/Int32/float PCM 复制并转换为归一化浮点数组。
多声道每帧保留振幅最大的声道，避免反相抵消；这是波形数据，不是用于播放的单声道混音。
`samplesReady(samples, rate)` 分块输出；完成时先发出 `decoded(samples, rate)`，
再发出 `finished()`。解码类会在内存保留整段采样。`stop()` 取消且不发完成信号；
再次 `decode()` 会取消并替换旧请求。错误通过 `errorOccurred` 报告。
可解码格式取决于 Qt 后端和编解码器，不保证所有 MP3/AAC 文件均可读取。

`FilledPushButton` 和 `FilledToolButton` 的浅色常态填充采用 Fluent 语义色
（中性、成功、警告、错误）；Attention 跟随主题色。原有暗色配色和悬停/按下的
半透明黑白背景保持不变。

`FlyoutDialog` 提供自定义内容区域和底部确认/取消图标按钮。
底栏高度为 40 逻辑像素，悬停区域撑满各自半边，不显示按钮提示，分割线为 2px；
正文按实际弹窗宽度计算换行高度，避免多余留白。
通过 `addWidget()` 添加控件、`showAt(target, parent)` 弹出，连接 `accepted` / `rejected`
处理结果；点击外部关闭按取消处理。复用 Flyout 的定位、阴影和动画，关闭后自动删除。
Buttons 页面提供 Show dialog 示例。

`TimeLineWidget` 提供分组标题、状态图标、连接线和圆角条目卡片。
通过 `addGroup(title, InfoBarIcon.SUCCESS)` 创建分组，再调用 `group.addItem(text, icon)`
添加条目；支持富文本、自动换行、动态移除分组和条目。TimeLine 展示页包含已完成、今日安排和待办事项。
每个 `TimeLineItem` 继承 `CardWidget`，复用背景、边框以及悬停/按下动画；
整张事项卡片（图标、文字和留白）均可点击，连接 `item.clicked` 处理业务操作。
聚焦后 Enter / Space 也可触发；`setClickEnabled(False)` 可关闭点击，保留展示内容。
文字仍支持富文本和完成态删除线，但作为整卡展示，不单独响应文字链接点击。
默认最大宽度为 370 逻辑像素，事项卡片宽 328px、单行高 50px，同组卡片间距 19px；
长文本自动换行并增加高度，不强制裁切。可通过 `setMaximumWidth()` / `setFixedWidth()` 自定义宽度。

`FilledFluentWindow` 提供默认展开的侧边栏、主题色填充的选中项和搜索框。
沿用 `FluentWindow` 的 `addSubInterface()` / `switchTo()` 接口，
搜索框自动搜索已注册页面的导航名称，点击结果或使用方向键和回车跳转。
按 Esc 关闭结果列表，清空输入不会改变当前页面；页面增删会同步更新搜索结果。
运行 `main.py`，在主页点击“打开 FilledFluentWindow 窗口”，
即可体验页面切换、搜索，以及设置页中的主题和自定义主题色切换。


## 按需导入与 Nuitka 打包

部分组件刻意不在包的 `__init__.py` 中统一导出，**不是漏实现**。统一入口中的导入可能让
Nuitka 把未使用的可选依赖纳入编译图；只有业务使用相应功能时，才从具体模块导入。

| 可选功能 | 按需导入模块 | 相关依赖 |
| --- | --- | --- |
| `ChartWidget` | `qfluentwidgets_pro.components.widgets.chart_widget` | QtWebEngine、QtQuickWidgets 及相关 Qt 运行库 |
| `CodeEdit`、`CodeLanguage` | `qfluentwidgets_pro.components.widgets.code_edit` | Pygments 语言解析器 |
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
音频波形展示页，包含文件解码/播放所需的 QtMultimedia。
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
