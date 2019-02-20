import os as _os

_path = _os.path.abspath(_os.path.join(
    _os.path.dirname(__file__), 'tesseract', 'bin') + ";") + _os.environ['PATH']

_os.environ['PATH'] = _path

from . import tesseractwrap
from .engine import Engine
from .reader import Reader

__all__ = [
    "Reader",
    "Engine",
    "tesseractwrap",
]
