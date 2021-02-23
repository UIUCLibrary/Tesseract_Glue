import pytest
import os

from uiucprescon import ocr


def test_invalid_tesseract_data_path():

    with pytest.raises(FileNotFoundError):

        reader = ocr.Reader(
            language_code="eng",
            tesseract_data_path="c:\\invalid_path"
        )
