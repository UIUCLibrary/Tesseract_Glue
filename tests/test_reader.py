import pytest

from uiucprescon import ocr


def test_invalid_tesseract_data_path():

    with pytest.raises(FileNotFoundError):

        reader = ocr.Reader(
            language_code="eng",
            tesseract_data_path="c:\\invalid_path"
        )


def test_invalid_image_throws_error(tessdata_eng):

    with pytest.raises(RuntimeError):

        reader = ocr.Reader(
            language_code="eng",
            tesseract_data_path=tessdata_eng
        )
        reader.read_image(None)
