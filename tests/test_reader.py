import pytest
import os

from uiucprescon import ocr


def test_invalid_tesseract_data_path():

    with pytest.raises(FileNotFoundError):

        reader = ocr.Reader(
            language_code="eng",
            tesseract_data_path="c:\\invalid_path"
        )


def test_read_image(tessdata_eng, sample_images):
    reader = ocr.Reader(
        language_code="eng",
        tesseract_data_path=tessdata_eng
    )
    sample_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
    image = ocr.load_image(sample_image)
    data = reader.read_image(image)
    assert isinstance(data, str)
