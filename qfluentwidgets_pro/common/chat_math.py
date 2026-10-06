"""Opt-in, offline formula rasterizer. No WebEngine or external TeX process."""

from functools import lru_cache
from io import BytesIO

from PySide6.QtGui import QImage


@lru_cache(maxsize=256)
def _formula_png(expression, color, pointSize):
    # Keep Matplotlib/NumPy out of plain-text chats and lightweight imports.
    from matplotlib.font_manager import FontProperties
    from matplotlib.mathtext import math_to_image
    from matplotlib import rc_context

    if len(expression) > 4096:
        raise ValueError('Formula exceeds the 4096-character rendering limit')
    output = BytesIO()
    # math_to_image uses Figure.savefig: its default white figure background
    # would hide pale formula glyphs in dark bubbles. Restore rcParams on exit.
    with rc_context({'savefig.transparent': True}):
        math_to_image('$' + expression.strip() + '$', output,
                      prop=FontProperties(size=pointSize), dpi=192,
                      format='png', color=color)
    return output.getvalue()


def renderFormula(expression, color='#202020', pointSize=12):
    """Return a high-DPI QImage using MathText's LaTeX subset.

    Requires Matplotlib. Unsupported syntax raises ValueError; the widget keeps
    the original expression visible. Callers can supply a different renderer.
    """
    image = QImage.fromData(_formula_png(expression, color, pointSize), 'PNG')
    image.setDevicePixelRatio(2)
    return image
