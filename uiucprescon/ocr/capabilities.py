"""Info about what is possible with the current build."""

from uiucprescon.ocr import tesseractwrap


def image_lib_versions():
    """Get the libraries Leptonica linked to .

    Returns:

    """
    data = tesseractwrap.get_image_lib_versions()

    def spliter(item: str):
        return tuple(item.strip().split(" "))

    return {
        key: value for key, value in map(spliter, data.split(":"))
            }
