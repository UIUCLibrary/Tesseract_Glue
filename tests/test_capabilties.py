import pytest

from uiucprescon import ocr


@pytest.fixture
def linked_image_libs():
    return ocr.image_lib_versions()


@pytest.mark.parametrize("library_name", ['libopenjp2', 'libtiff'])
def test_expected_decoders(linked_image_libs, library_name):
    assert library_name in linked_image_libs
