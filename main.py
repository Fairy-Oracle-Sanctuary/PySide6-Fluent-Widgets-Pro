"""Entry point for the migrated free gallery, with a separate chart window."""

import os
import sys

from PySide6.QtCore import Qt, QTranslator
from PySide6.QtWidgets import QApplication

from gallery.common.config import cfg
from gallery.view.main_window import MainWindow
from qfluentwidgets_pro import FluentTranslator


def createApplication(argv=None):
    """Configure scale and install both widget and gallery translations."""
    if cfg.get(cfg.dpiScale) != 'Auto':
        os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'
        os.environ['QT_SCALE_FACTOR'] = str(cfg.get(cfg.dpiScale))
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    app = QApplication(sys.argv if argv is None else argv)
    locale = cfg.get(cfg.language).value
    fluentTranslator = FluentTranslator(locale)
    galleryTranslator = QTranslator(app)
    galleryTranslator.load(locale, 'gallery', '.', ':/gallery/i18n')
    app.installTranslator(fluentTranslator)
    app.installTranslator(galleryTranslator)
    app._galleryTranslators = (fluentTranslator, galleryTranslator)
    return app


if __name__ == '__main__':
    app = createApplication()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
