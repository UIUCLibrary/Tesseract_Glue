import os
import pytest
from uiucprescon import ocr


@pytest.mark.integration
def test_reader(tessdata_eng, sample_images):
    reader = ocr.Reader(language_code="eng", tesseract_data_path=tessdata_eng)
    test_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")

    text = reader.read(test_image)
    assert isinstance(text, str)
