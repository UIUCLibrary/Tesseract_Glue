import os
import shutil
import urllib.request
from tempfile import TemporaryDirectory

import pytest
from uiucprescon import ocr

TESSDATA_SOURCE_URL = "https://github.com/tesseract-ocr/tessdata/raw/3.04.00/"


def download_data(url, destination):
    with TemporaryDirectory() as download_path:
        base_name = os.path.basename(url)
        destination_file = os.path.join(destination, base_name)

        if os.path.exists(destination_file):
            return

        # if not os.path.exists()
        print("Downloading {}".format(url))
        test_file_path = os.path.join(download_path, base_name)

        urllib.request.urlretrieve(url, filename=test_file_path)
        if not os.path.exists(test_file_path):
            raise FileNotFoundError(
                "Failure to download file from {}".format(url))

        shutil.move(test_file_path, destination)


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

