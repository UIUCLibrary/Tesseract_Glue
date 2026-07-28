"""Info about what is possible with the current build."""

from typing import Mapping
from uiucprescon.ocr import tesseractwrap

__all__ = ["image_lib_versions"]


def parse_version(data: str) -> Mapping[str, str]:
    """Parse the version string returned by tesseract."""
    return {
        chunk.strip().split(" ")[0]: " ".join(chunk.strip().split(" ")[1:])
        for chunk in data.split(":")
    }


def image_lib_versions() -> Mapping[str, str]:
    """Get the libraries Leptonica linked to .

    Returns:
        Returns libraries and their versions

    """
    data = tesseractwrap.get_image_lib_versions()
    return parse_version(data)
