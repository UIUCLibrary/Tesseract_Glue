"""Optical character recognition that Use Google Tesseract."""
import os as _os

# the path to the linking shared libraries need to added to the path env var
# to properly work
_paths = list(filter(lambda i: i.strip(), _os.environ['PATH'].split(";")))

_tesseract_path = _os.path.abspath(
    _os.path.join(_os.path.dirname(__file__), 'tesseract', 'bin'))

for p in _paths:
    if p == _tesseract_path:
        break
else:
    _paths.insert(0, _tesseract_path)

_os.environ['PATH'] = ";".join(_paths)
# pylint: disable=wrong-import-position
from . import tesseractwrap             # noqa: E402
from .tesseractwrap import load_image   # noqa: E402
from .engine import Engine              # noqa: E402
from .reader import Reader              # noqa: E402
from .languages import LANGUAGE_CODES   # noqa: E402
from .capabilities import image_lib_versions
__all__ = [
    "Reader",
    "Engine",
    "image_lib_versions",
    "tesseractwrap",
    "LANGUAGE_CODES",
    "load_image"
]
