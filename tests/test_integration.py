import os
import pytest
from uiucprescon import ocr
from .conftest import download_data

TESSDATA_SOURCE_URL = "https://github.com/tesseract-ocr/tessdata/raw/3.04.00/"

@pytest.mark.integration
def test_reader_with_data(tessdata_eng, sample_images):
    reader = ocr.Reader(language_code="eng", tesseract_data_path=tessdata_eng)
    test_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")

    text = reader.read(test_image)
    assert isinstance(text, str)


@pytest.mark.integration
def test_no_osd_file():
    english_data_url = "{}{}".format(TESSDATA_SOURCE_URL, "eng.traineddata")

    test_path = os.path.dirname(__file__)
    tessdata_path = os.path.join(test_path, "no_osd_tessdata")

    if not os.path.exists(tessdata_path):
        os.makedirs(tessdata_path)
    download_data(english_data_url, destination=tessdata_path)
    with pytest.raises(FileNotFoundError):

        reader = ocr.Reader(
            language_code="eng",
            tesseract_data_path=tessdata_path
        )

