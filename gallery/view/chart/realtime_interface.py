# coding: utf-8
"""Real-time chart update demo interface"""

import random

from PySide6.QtCore import QTimer

from qfluentwidgets_pro import ChartWidget, PushButton

from ..gallery_interface import GalleryInterface


class RealtimeChartInterface(GalleryInterface):
    """Demo interface for real-time data updates with animation control"""

    def __init__(self, parent=None):
        super().__init__(
            title="实时数据更新",
            subtitle="qfluentwidgets_pro.components.chart_widget",
            parent=parent,
        )
        self.setObjectName("realtimeInterface")

        # Create chart widget
        self.chart = ChartWidget(self.view)
        self.chart.setFixedHeight(400)
        self.chart.setFixedWidth(400)

        # Initial data
        self.data_count = 12
        self.x_data = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.y_data = [random.randint(100, 500) for _ in range(7)]

        # Set initial option
        self._updateChartOption()

        # Animation control buttons
        self.animationEnabled = True
        self.animBtn = PushButton("禁用动画", self.view)
        self.animBtn.setFixedWidth(120)
        self.animBtn.clicked.connect(self._toggleAnimation)

        self.startBtn = PushButton("开始实时更新", self.view)
        self.startBtn.setFixedWidth(120)
        self.startBtn.clicked.connect(self._toggleRealtimeUpdate)

        self.stopBtn = PushButton("停止更新", self.view)
        self.stopBtn.setFixedWidth(120)
        self.stopBtn.clicked.connect(self._stopRealtimeUpdate)
        self.stopBtn.setEnabled(False)

        # Timer for real-time updates
        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self._onRealtimeUpdate)

        # Add to layout
        self.vBoxLayout.addWidget(self.chart)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.animBtn)
        self.vBoxLayout.addWidget(self.startBtn)
        self.vBoxLayout.addWidget(self.stopBtn)

        self.enableTransparentBackground()

    def _updateChartOption(self):
        """Update chart with current data"""
        self.chart.setOption(
            {
                "title": {"text": "实时数据演示", "subtext": "模拟实时数据流"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": self.x_data},
                "yAxis": {"type": "value"},
                "series": [{"name": "数据", "type": "bar", "data": self.y_data}],
            }
        )

    def _toggleAnimation(self):
        """Toggle animation on/off"""
        self.animationEnabled = not self.animationEnabled
        self.chart.setAnimationEnabled(self.animationEnabled)
        self.animBtn.setText("启用动画" if not self.animationEnabled else "禁用动画")

    def _toggleRealtimeUpdate(self):
        """Start real-time updates"""
        self.updateTimer.start(100)  # Update every 100ms
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)

    def _stopRealtimeUpdate(self):
        """Stop real-time updates"""
        self.updateTimer.stop()
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)

    def _onRealtimeUpdate(self):
        """Handle real-time update tick"""
        # Shift data and add new random value
        self.y_data.pop(0)
        self.y_data.append(random.randint(100, 500))
        self._updateChartOption()
