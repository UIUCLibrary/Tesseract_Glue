import os as _os
import sys as _sys

_path = _os.path.abspath(_os.path.join(
    _os.path.dirname(__file__), 'tesseract', 'bin')) + ";" + _os.environ['PATH']
_os.environ['PATH'] = _path

try:
    from . import tesseractwrap
except ImportError as e:
    print("Check path values", file=_sys.stderr)
    for k, v in _os.environ.items():
        print("{}:{}".format(k, v), file=_sys.stderr)
    raise


from .engine import Engine
from .reader import Reader
from .languages import LANGUAGE_CODES

__all__ = [
    "Reader",
    "Engine",
    "tesseractwrap",
    "LANGUAGE_CODES"
]
