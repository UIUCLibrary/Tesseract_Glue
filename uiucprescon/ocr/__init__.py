import os as _os
from .engine import Engine
from . import tesseractwrap
from .reader import Reader

_path = _os.path.join(
    _os.path.dirname(__file__), 'tesseract', 'bin') + ";" + _os.environ['PATH']

_os.environ['PATH'] = _path


__all__ = [
    "Reader",
    "Engine",
    "tesseractwrap",
]
