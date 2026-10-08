"""Offscreen search regressions for both hierarchical combo boxes."""
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QModelIndex, QPoint, Qt, QTranslator
from PySide6.QtGui import QImage, QStandardItem, QStandardItemModel
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets_pro import TreeComboBox, MultiSelectionTreeComboBox, Theme, setTheme


def run():
    app = QApplication([])
    for dark in (False, True):
        setTheme(Theme.DARK if dark else Theme.LIGHT)
        for rtl in (False, True):
            for cls in (TreeComboBox, MultiSelectionTreeComboBox):
                box = cls()
                box.resize(400, 36)
                box.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
                root = box.addItem("京都动画")
                nested = box.addItem("Sound!", root)
                leaf = box.addItem("Kumiko", nested)
                hidden = box.addItem("Reina", nested)
                other = box.addItem("Other studio")
                box.addItem("Other show", other)
                multi = isinstance(box, MultiSelectionTreeComboBox)
                changes, searches = [], []
                if multi:
                    box.setSelectedIndexes([hidden])
                    box.selectionChanged.connect(changes.append)
                else:
                    box.setCurrentModelIndex(hidden)
                    box.currentModelIndexChanged.connect(changes.append)
                box.searchTextChanged.connect(searches.append)
                box.show()
                box.showPopup()
                QTest.qWait(180)
                tree, edit = box._tree, box.searchLineEdit()
                proxy = box._viewModel
                mapped = proxy.mapFromSource
                assert edit.isVisible()
                assert edit.height() == 30 and edit.font().pixelSize() == 12
                tree.collapse(mapped(nested))
                edit.setText("  kUMI  ")
                assert box.searchText() == "  kUMI  " and searches == ["  kUMI  "]
                assert not tree.isRowHidden(root.row(), QModelIndex())
                assert not tree.isRowHidden(leaf.row(), mapped(nested))
                assert tree.isRowHidden(hidden.row(), mapped(nested))
                assert tree.isRowHidden(other.row(), QModelIndex())
                assert tree.isExpanded(mapped(nested))
                assert not changes
                assert (box.selectedIndexes() == [hidden] if multi else box.currentModelIndex() == hidden)
                raster = QImage(tree.viewport().size(), QImage.Format_ARGB32_Premultiplied)
                raster.fill(Qt.transparent)
                tree.viewport().render(raster, QPoint(), renderFlags=QWidget.DrawChildren)
                assert any(
                    (c := raster.pixelColor(x, y)).alpha() > 0
                    and c.red() > 150 and c.green() > 100 and c.blue() < 110
                    for y in range(raster.height()) for x in range(raster.width())
                ), "Missing literal match highlight"
                edit.clearButton.click()
                assert box.searchText() == "" and not tree.isExpanded(mapped(nested))
                assert not tree.isRowHidden(hidden.row(), mapped(nested))
                box.setSearchText("动画")
                assert not tree.isRowHidden(hidden.row(), mapped(nested))
                assert tree.isRowHidden(other.row(), QModelIndex())
                box.setSearchText("missing")
                assert not tree.isVisible() and box._emptySearch.isVisible()
                box.model().setData(leaf, "missing <literal>")
                assert tree.isVisible()
                inserted = box.addItem("missing two", other)
                assert not tree.isRowHidden(other.row(), QModelIndex())
                box.model().removeRow(inserted.row(), other)
                assert tree.isRowHidden(other.row(), QModelIndex())
                if multi:
                    box._setDescendantsSelected(root, True)
                    assert set(box.selectedIndexes()) == {leaf, hidden}
                    assert mapped(root).data(Qt.CheckStateRole) == Qt.Checked
                QTest.keyClick(edit, Qt.Key_Down)
                assert tree.hasFocus()
                edit.setFocus()
                QTest.keyClick(edit, Qt.Key_Escape)
                assert not box._popup.isVisible()
                box.setSearchEnabled(False)
                box.showPopup()
                assert not edit.isVisible() and box.searchText() == ""
                assert not tree.isRowHidden(other.row(), QModelIndex())
                box.setSearchEnabled(True)
                box.setSearchText("missing")
                box.showPopup()
                assert edit.isVisible() and tree.isVisible()
                replacement = QStandardItemModel(box)
                replacement.appendRow(QStandardItem("new tree"))
                box.setModel(replacement)
                box.showPopup()
                assert not tree.isVisible()
                box.setSearchText("")
                assert tree.isVisible() and not tree.isRowHidden(0, QModelIndex())
                box.hidePopup()
                box.close()
                box.deleteLater()
                app.processEvents()
    translator = QTranslator()
    assert translator.load(":/qfluentwidgets/i18n/qfluentwidgets.zh_CN.qm")
    app.installTranslator(translator)
    for cls in (TreeComboBox, MultiSelectionTreeComboBox):
        box = cls()
        box.addItem("example")
        box.show()
        box.showPopup()
        assert box.searchLineEdit().placeholderText() == "搜索条目"
        box.setSearchText("not present")
        assert box._emptySearch.text() == "没有匹配的条目"
        box.hidePopup()
        box.close()
        box.deleteLater()
        app.processEvents()
    app.removeTranslator(translator)
    print("Tree combo search: 8 theme/direction/selection combinations passed")


if __name__ == "__main__":
    run()
