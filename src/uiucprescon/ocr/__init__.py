"""Optical character recognition that Use Google Tesseract."""

from . import utils
from . import tesseractwrap
from .tesseractwrap import load_image
from .tesseractwrap import PDFBuilder
from .tesseractwrap import OCRApi
from .engine import Engine
from .reader import Reader
from .languages import LANGUAGE_CODES
from .capabilities import image_lib_versions

__all__ = [
    "Reader",
    "Engine",
    "image_lib_versions",
    "tesseractwrap",
    "LANGUAGE_CODES",
    "load_image",
    "OCRApi",
    "PDFBuilder",
    "utils"
]
