# coding:utf-8
from typing import Union

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QIcon, QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QWidget

from ...common.icon import FluentIconBase
from .navigation_widget import NavigationWidget
from .top_navigation_panel import (
    TopNavigationDisplayMode,
    TopNavigationItemPosition,
    TopNavigationPanel,
    TopNavigationPushButton,
)


class TopNavigationInterface(QWidget):
    """Top navigation interface (horizontal)"""

    displayModeChanged = TopNavigationPanel.displayModeChanged

    def __init__(self, parent=None, showReturnButton=False):
        """
        Parameters
        ----------
        parent: widget
            parent widget

        showReturnButton: bool
            whether to show return button
        """
        super().__init__(parent=parent)
        self.panel = TopNavigationPanel(self)
        self.panel.setReturnButtonVisible(showReturnButton)
        self.panel.installEventFilter(self)
        self.panel.displayModeChanged.connect(self.displayModeChanged)

        # add layout to contain the panel
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.addWidget(self.panel)

        self.setAttribute(Qt.WA_TranslucentBackground)

    def addItem(
        self,
        routeKey: str,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        onClick=None,
        selectable=True,
        position=TopNavigationItemPosition.LEFT,
        tooltip: str = None,
        expanded: bool = False,
    ) -> TopNavigationPushButton:
        """add navigation item

        Parameters
        ----------
        routKey: str
            the unique name of item

        icon: str | QIcon | FluentIconBase
            the icon of navigation item

        text: str
            the text of navigation item

        onClick: callable
            the slot connected to item clicked signal

        selectable: bool
            whether the item is selectable

        position: TopNavigationItemPosition
            where the button is added

        tooltip: str
            the tooltip of item

        expanded: bool
            whether to show text for this specific item
        """
        return self.insertItem(
            -1,
            routeKey,
            icon,
            text,
            onClick,
            selectable,
            position,
            tooltip,
            expanded,
        )

    def addWidget(
        self,
        routeKey: str,
        widget: NavigationWidget,
        onClick=None,
        position=TopNavigationItemPosition.LEFT,
        tooltip: str = None,
    ):
        """add custom widget

        Parameters
        ----------
        routKey: str
            the unique name of item

        widget: NavigationWidget
            the custom widget to be added

        onClick: callable
            the slot connected to item clicked signal

        position: TopNavigationItemPosition
            where the widget is added

        tooltip: str
            the tooltip of widget
        """
        self.insertWidget(-1, routeKey, widget, onClick, position, tooltip)

    def insertItem(
        self,
        index: int,
        routeKey: str,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        onClick=None,
        selectable=True,
        position=TopNavigationItemPosition.LEFT,
        tooltip: str = None,
        expanded: bool = False,
    ) -> TopNavigationPushButton:
        """insert navigation item

        Parameters
        ----------
        index: int
            insert position

        routKey: str
            the unique name of item

        icon: str | QIcon | FluentIconBase
            the icon of navigation item

        text: str
            the text of navigation item

        onClick: callable
            the slot connected to item clicked signal

        selectable: bool
            whether the item is selectable

        position: TopNavigationItemPosition
            where the item is added

        tooltip: str
            the tooltip of item

        expanded: bool
            whether to show text for this specific item
        """
        w = self.panel.insertItem(
            index,
            routeKey,
            icon,
            text,
            onClick,
            selectable,
            position,
            tooltip,
            expanded,
        )
        self.setMinimumWidth(self.panel.layoutMinWidth())
        return w

    def insertWidget(
        self,
        index: int,
        routeKey: str,
        widget: NavigationWidget,
        onClick=None,
        position=TopNavigationItemPosition.LEFT,
        tooltip: str = None,
    ):
        """insert custom widget

        Parameters
        ----------
        index: int
            insert position

        routKey: str
            the unique name of item

        widget: NavigationWidget
            the custom widget to be added

        onClick: callable
            the slot connected to item clicked signal

        position: TopNavigationItemPosition
            where the widget is added

        tooltip: str
            the tooltip of widget
        """
        self.panel.insertWidget(index, routeKey, widget, onClick, position, tooltip)
        self.setMinimumWidth(self.panel.layoutMinWidth())

    def removeWidget(self, routeKey: str):
        """remove widget

        Parameters
        ----------
        routKey: str
            the unique name of item
        """
        self.panel.removeWidget(routeKey)

    def setCurrentItem(self, name: str):
        """set current selected item

        Parameters
        ----------
        name: str
            the unique name of item
        """
        self.panel.setCurrentItem(name)

    def expand(self, useAni=True):
        """expand navigation panel (show text)"""
        self.panel.expand(useAni)

    def collapse(self, useAni=True):
        """collapse navigation panel (hide text)"""
        self.panel.collapse(useAni)

    def toggle(self):
        """toggle navigation panel"""
        self.panel.toggle()

    def setReturnButtonVisible(self, isVisible: bool):
        """set whether the return button is visible"""
        self.panel.setReturnButtonVisible(isVisible)

    def isIndicatorAnimationEnabled(self):
        return self.panel.isIndicatorAnimationEnabled()

    def setIndicatorAnimationEnabled(self, isEnabled: bool):
        """set whether the indicator sliding animation is enabled"""
        self.panel.setIndicatorAnimationEnabled(isEnabled)

    def setItemExpanded(self, routeKey: str, expanded: bool):
        """set whether a specific item shows its text

        Parameters
        ----------
        routeKey: str
            the route key of the item

        expanded: bool
            whether to show text for this item
        """
        self.panel.setItemExpanded(routeKey, expanded)

    def widget(self, routeKey: str):
        return self.panel.widget(routeKey)

    def eventFilter(self, obj, e: QEvent):
        if obj is not self.panel or e.type() != QEvent.Resize:
            return super().eventFilter(obj, e)

        if self.panel.displayMode != TopNavigationDisplayMode.MENU:
            event = QResizeEvent(e)
            if event.oldSize().height() != event.size().height():
                self.setFixedHeight(event.size().height())

        return super().eventFilter(obj, e)

    def resizeEvent(self, e: QResizeEvent):
        if e.oldSize().width() != self.width():
            self.panel.setFixedWidth(self.width())
