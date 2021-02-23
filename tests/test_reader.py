import pytest
import os

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

def test_valid_image(tessdata_eng, sample_images):

    sample_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
    reader = ocr.Reader(
        language_code="eng",
        tesseract_data_path=tessdata_eng
    )
    image = reader.read_image(sample_image)
    assert image is not None
