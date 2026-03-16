# coding:utf-8
from typing import Union

from PySide6.QtCore import QFileInfo, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFileDialog, QVBoxLayout, QWidget

from ...common.color import isDarkTheme
from ...common.font import setFont
from ..widgets.button import HyperlinkButton
from ..widgets.label import BodyLabel


class DropMultiFilesWidget(QWidget):
    """get drag folder widget"""

    draggedChange = Signal(list)
    selectionChange = Signal(list)

    def __init__(self, defaultDir=".\\", isDashLine=True, parent=None):
        super().__init__(parent)
        self.__borderWidth: int = 2
        self._defaultDir: str = defaultDir
        self.__lineColor: QColor = None
        self.__enableDashLine: bool = isDashLine
        self.viewLayout: QVBoxLayout = QVBoxLayout(self)
        self.setAcceptDrops(True)
        self.setMinimumSize(QSize(256, 200))

        self.__initWidget()
        self.button.clicked.connect(self._showDialog)

    def __initWidget(self):
        self.label: BodyLabel = BodyLabel(self.tr("Drag & drop any files here"), self)
        self.orLabel: BodyLabel = BodyLabel(self.tr("or"), self)
        self.button: HyperlinkButton = HyperlinkButton(
            "", self.tr("Browse files"), self
        )

        self.label.setAlignment(Qt.AlignHCenter)
        self.orLabel.setAlignment(Qt.AlignHCenter)

        for w in [self.button, self.label, self.orLabel]:
            setFont(w, 15)

        self.viewLayout.setAlignment(Qt.AlignCenter)
        self.viewLayout.addWidget(self.label)
        self.viewLayout.addWidget(self.orLabel)
        self.viewLayout.addWidget(self.button)

    def _showDialog(self) -> None:
        self.selectionChange.emit(
            [
                QFileDialog.getExistingDirectory(
                    self, self.tr("Browse files"), self._defaultDir
                )
            ]
        )

    def setLabelText(self, text) -> None:
        self.label.setText(text)

    def setDefaultDir(self, dir: str) -> None:
        self._defaultDir = dir

    def setBorderColor(self, color: Union[str, QColor]) -> None:
        if isinstance(color, str):
            color = QColor(color)
        if self.__lineColor == color:
            return
        self.__lineColor = color
        self.update()

    def enableDashLine(self, isEnable: bool) -> None:
        if self.__enableDashLine == isEnable:
            return
        self.__enableDashLine = isEnable
        self.update()

    def setBorderWidth(self, width: int) -> None:
        if self.__borderWidth == width:
            return
        self.__borderWidth = width
        self.update()

    def borderWidth(self) -> int:
        return self.__borderWidth

    def defaultDir(self) -> str:
        return self._defaultDir

    def isDashLine(self) -> bool:
        return self.__enableDashLine

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            c = 255 if isDarkTheme() else 0
            color = QColor(c, c, c, 32)
        elif self.__lineColor:
            color = self.__lineColor
        else:
            color = (
                QColor(255, 255, 255, 120) if isDarkTheme() else QColor(0, 0, 0, 100)
            )
        pen = QPen(color)
        pen.setWidth(self.borderWidth())
        if self.__enableDashLine:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern([4, 4])
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 16, 16)

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        if event.mimeData().hasUrls:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        super().dropEvent(event)
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        dirPath = []
        if urls:
            for url in urls:
                if QFileInfo(url).isDir():
                    dirPath.append(url)
            self.draggedChange.emit(dirPath)
        event.acceptProposedAction()


class DropSingleFileWidget(DropMultiFilesWidget):
    """get dray file widget"""

    def __init__(self, defaultDir=".\\", fileFilter=None, isDashLine=True, parent=None):
        """Multiple file types are separated by ';;'"""
        super().__init__(defaultDir, isDashLine, parent)
        self.setLabelText(self.tr("Drag & drop any file here"))
        self.button.setText(self.tr("Browse file"))
        self._fileFilter = (
            self.tr("All files (*.*);; Text files (*.txt)")
            if fileFilter is None
            else fileFilter
        )

    def _showDialog(self):
        return self.selectionChange.emit(
            QFileDialog.getOpenFileNames(
                self, self.tr("Browse file"), self._defaultDir, self._fileFilter
            )[0]
        )

    def setFileFilter(self, filter: str) -> None:
        """Multiple file types are separated by ';;'"""
        self._fileFilter = filter

    def fileFilter(self) -> str:
        return self._fileFilter

    def dropEvent(self, event):
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        filePath = []
        if urls:
            for url in urls:
                if not QFileInfo(url).isDir():
                    filePath.append(url)
            self.draggedChange.emit(filePath)
        event.acceptProposedAction()


class DropSingleFolderWidget(DropMultiFilesWidget):
    """Single folder selector (drag or click to select one folder)"""

    def __init__(self, defaultDir=".\\", isDashLine=True, parent=None):
        super().__init__(defaultDir, isDashLine, parent)
        self.setLabelText(self.tr("Drag & drop a folder here"))
        self.button.setText(self.tr("Browse folder"))

    def dropEvent(self, event):
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        folderPath = []
        if urls:
            for url in urls:
                if QFileInfo(url).isDir():
                    folderPath.append(url)
                    break  # 只取第一个文件夹
            self.draggedChange.emit(folderPath)
        event.acceptProposedAction()


class DropMultiFoldersWidget(DropMultiFilesWidget):
    """Multiple folders selector (drag or click to select multiple folders)"""

    def __init__(self, defaultDir=".\\", isDashLine=True, parent=None):
        super().__init__(defaultDir, isDashLine, parent)
        self.setLabelText(self.tr("Drag & drop folders here"))
        self.button.setText(self.tr("Browse folder"))

    def _showDialog(self) -> None:
        """Open dialog to select multiple folders"""
        dialog = QFileDialog(self, self.tr("Browse folder"), self._defaultDir)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)

        listView = dialog.findChild(QWidget, "listView")
        if listView:
            listView.setSelectionMode(3)

        if dialog.exec():
            folders = dialog.selectedFiles()
            self.selectionChange.emit(folders)

    def dropEvent(self, event):
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        folderPaths = []
        if urls:
            for url in urls:
                if QFileInfo(url).isDir():
                    folderPaths.append(url)
            self.draggedChange.emit(folderPaths)
        event.acceptProposedAction()
