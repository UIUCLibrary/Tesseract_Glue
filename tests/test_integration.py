import os
import pytest
import ocr


@pytest.mark.integration
def test_reader(download_sample_images):
    reader = ocr.Reader(language_code="eng")

    test_image = os.path.join(
        download_sample_images, "IlliniLore_1944_00000011.tif")

    text = reader.read(test_image)
    assert isinstance(text, str)
