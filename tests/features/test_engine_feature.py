import os

from uiucprescon import ocr
from pytest_bdd import scenario, given, then, when
import re


@scenario("engine.feature", 'Uses an engine to read the data')
def test_engine_feature():
    pass


@given("a directory contains the english tesseract data", target_fixture='tess_path')
def tess_path(tessdata_eng):
    assert os.path.exists(tessdata_eng)
    tessdata_eng_file = os.path.join(tessdata_eng, "eng.traineddata")
    assert os.path.exists(tessdata_eng_file)
    return tessdata_eng


@given("a directory contains an image containing english text", target_fixture='image_path')
def image_path(sample_images):
    test_image = os.path.join(
        sample_images, "IlliniLore_1944_00000011.tif")
    assert os.path.exists(test_image)

    return test_image


@given("an engine is created", target_fixture='ocr_engine')
def ocr_engine(tess_path):
    tess_engine = ocr.Engine(tess_path)
    return tess_engine


@then("the engine can produce a reader object can get the text from the image")
def read_ocr(ocr_engine, image_path):
    reader = ocr_engine.get_reader("eng")
    # print(reader)
    data = reader.read(image_path)
    assert data
    pass
    # raise NotImplementedError(
    #     u'STEP: Then the engine can produce an english reader object')


@when("the engine has version information")
def ocr_engine_has_version(ocr_engine):
    e = ocr_engine
    version = e.get_version()
    version_regex = re.compile("[0-9][.][0-9]{1,2}[.][0-9]{1,2}")
    print(version)
    assert version_regex.match(version)


@when("a reader is created")
def step_impl():
    pass
    # raise NotImplementedError(u'STEP: When a reader is created')