import os as _os
_paths = list(filter(lambda i: i.strip(), _os.environ['PATH'].split(";")))

_tesseract_path = _os.path.abspath(
    _os.path.join(_os.path.dirname(__file__), 'tesseract', 'bin'))

for p in _paths:
    if p == _tesseract_path:
        break
else:
    _paths.insert(0, _tesseract_path)

_os.environ['PATH'] = ";".join(_paths)

from . import tesseractwrap
from .engine import Engine
from .reader import Reader
from .languages import LANGUAGE_CODES

__all__ = [
    "Reader",
    "Engine",
    "tesseractwrap",
    "LANGUAGE_CODES"
]
