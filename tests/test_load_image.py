from uiucprescon import ocr
import os

def test_load_image(sample_images):
    sample_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
    image = ocr.load_image(sample_image)
    assert isinstance(image.w, int) and  isinstance(image.h, int)
