import pytest
import os

from uiucprescon import ocr


def test_invalid_tesseract_data_path():

    with pytest.raises(FileNotFoundError):

        reader = ocr.Reader(
            language_code="eng",
            tesseract_data_path="c:\\invalid_path"
        )


def test_invalid_tesseract_language(tessdata_eng):
    with pytest.raises(FileNotFoundError):
        reader = ocr.Reader(
            language_code="spam",
            tesseract_data_path=tessdata_eng
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


def test_read_image_invalid_raises(tessdata_eng, capfd):
    reader = ocr.Reader(
        language_code="eng",
        tesseract_data_path=tessdata_eng
    )
    with pytest.raises(Exception):
        reader.read("invalid_file.tif")
    out, err = capfd.readouterr()
    assert 'image file not found: invalid_file.tif' in err

