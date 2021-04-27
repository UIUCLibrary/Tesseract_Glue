"""Info about what is possible with the current build."""

from uiucprescon.ocr import tesseractwrap
from typing import Mapping, Tuple


def image_lib_versions() -> Mapping[str, str]:
    """Get the libraries Leptonica linked to .

    Returns:
        Returns libraries and their versions

    """
    data = tesseractwrap.get_image_lib_versions()

    def spliter(item: str) -> Tuple[str, ...]:
        return tuple(item.strip().split(" "))

    return {key: value for key, value in map(spliter, data.split(":"))}
