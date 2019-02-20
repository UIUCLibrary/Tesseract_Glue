import os as _os
import sys as _sys
_paths = list(filter(lambda i: i.strip(), _os.environ['PATH'].split(";")))
_tesseract_path = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), 'tesseract', 'bin'))

for p in _paths:
    if p == _tesseract_path:
        break
else:
    _paths .insert(0, _tesseract_path)

_os.environ['PATH'] = ";".join(_paths)

try:
    from . import tesseractwrap
except ImportError as e:
    import subprocess
    print("Check path values", file=_sys.stderr)
    for k, v in _os.environ.items():
        print("{}:{}".format(k, v), file=_sys.stderr)

    tesseract_exe = _os.path.join(_tesseract_path, "tesseract.exe")
    if not _os.path.exists(tesseract_exe):
        print("Did not find tesseract", file=_sys.stderr)
    subprocess.call([tesseract_exe, "--version"])

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
