"""Info about what is possible with the current build."""

from typing import Mapping, Tuple
from uiucprescon.ocr import tesseractwrap


def image_lib_versions() -> Mapping[str, str]:
    """Get the libraries Leptonica linked to .

    Returns:
        Returns libraries and their versions

    """
    data = tesseractwrap.get_image_lib_versions()

    def spliter(item: str) -> Tuple[str, ...]:
        return tuple(item.strip().split(" "))

    return dict(map(spliter, data.split(":")))
