import os as _os

_path = _os.path.join(_os.path.dirname(__file__), 'tesseract', 'bin') + ";" + _os.environ['PATH']
_os.environ['PATH'] = _path

from .engine import Engine

from . import tesseractwrap
from .reader import Reader

__all__ = [
    "Reader",
    "Engine",
    "tesseractwrap",
]
