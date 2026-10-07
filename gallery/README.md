# Gallery

The free-gallery pages, components, styles, images and translations were migrated
from `PyQt-Fluent-Widgets/examples/gallery` (its PySide6 variant) by zhiyiYo.
They use this repository's `qfluentwidgets_pro` package; upstream attribution and
the repository's licensing terms remain applicable.

Run `py -3.9 main.py` from the repository root. **Charts** opens the existing
independent chart window with Mica and reuses it after closing/reopening.
QtWebEngine is loaded only on first use.

**Chat**, directly below Charts, opens a separate native Qt chat window with
the existing ChatWidget demo. It keeps message history on reopen and stops
simulated streaming when closed. No network/model service is called.

All 91 restored/extended components listed in the root README are registered by
`view/pro_examples.py` on the matching category pages. Previews are created on
first page visit; CodeEdit and AudioWaveformWidget require clicking **Load demo**
to import their optional dependencies. GuideWindow, TopFluentWindow and
FilledFluentWindow examples open reusable independent windows.

Interactive examples used by the gallery live in `pro_demos/`; the gallery does
not import test fixtures. `tests/gallery_fixtures` remains available for existing
component regression tests and screenshot renderers. Component code is unchanged.
