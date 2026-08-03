import os
from uiucprescon import ocr
def test_rsize_image(sample_images):

    sample_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
    image = ocr.load_image(sample_image)
    print(image)
    assert image.w == 1969
    smaller_image = ocr.utils.pixScaleToSize(image, 800, 0)
    assert smaller_image.w == 800
