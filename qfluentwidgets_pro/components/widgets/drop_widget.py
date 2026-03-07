# coding:utf-8
from typing import Union

from PySide6.QtCore import QSize, Signal, QFileInfo, Qt
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QFileDialog, QWidget, QVBoxLayout

from ...common.font import setFont
from ...common.color import isDarkTheme
from ..widgets.button import HyperlinkButton
from ..widgets.label import BodyLabel


class DropMultiFilesWidget(QWidget):
    """ get drag folder widget"""
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
        self.label: BodyLabel = BodyLabel(self.tr("拖动文件夹到此"), self)
        self.orLabel: BodyLabel = BodyLabel(self.tr("或"), self)
        self.button: HyperlinkButton = HyperlinkButton('', "选择文件夹", self)
        self.label.setAlignment(Qt.AlignHCenter)
        self.orLabel.setAlignment(Qt.AlignHCenter)
        
        for w in [self.button, self.label, self.orLabel]:
            setFont(w, 15)
        
        self.viewLayout.setAlignment(Qt.AlignCenter)
        self.viewLayout.addWidget(self.label)
        self.viewLayout.addWidget(self.orLabel)
        self.viewLayout.addWidget(self.button)

    def _showDialog(self) -> None:
        self.selectionChange.emit([QFileDialog.getExistingDirectory(self, "选择文件夹", self._defaultDir)])

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
            color = QColor(255, 255, 255, 120) if isDarkTheme() else QColor(0, 0, 0, 100)
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
    """ get dray file widget """
    def __init__(
            self,
            defaultDir=".\\",
            fileFilter="所有文件 (*.*);; 文本文件 (*.txt)",
            isDashLine=True,
            parent=None
    ):
        """ 多个文件类型用;;分开 """
        super().__init__(defaultDir, isDashLine, parent)
        self.setLabelText("拖动任意文件到此")
        self.button.setText("选择文件")
        self._fileFilter = fileFilter

    def _showDialog(self):
        return self.selectionChange.emit(
            QFileDialog.getOpenFileNames(self, "选择文件", self._defaultDir, self._fileFilter)[0]
        )
    
    def setFileFilter(self, filter: str) -> None:
        """ 多个文件类型用;;分开 [所有文件 (*.*);; 文本文件 (*.txt)] """
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