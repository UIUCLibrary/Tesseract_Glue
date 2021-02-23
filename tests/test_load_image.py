import os
import pytest
from uiucprescon import ocr

def test_load_image(sample_images):
    sample_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
    image = ocr.load_image(sample_image)
    assert isinstance(image.w, int) and isinstance(image.h, int)

def test_invalid_image_throws_error(tessdata_eng):

    with pytest.raises(RuntimeError):
        i = ocr.load_image("./not/a/file.tif")
        print(i)


def test_valid_image(tessdata_eng, sample_images):

    sample_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
    image = ocr.load_image(sample_image)
    assert image is not None
