import re

from uiucprescon import ocr
import types
import pytest

def test_import_module():
    assert isinstance(ocr, types.ModuleType)


def test_version():

    e = ocr.Engine("")
    version = e.get_version()
    version_regex = re.compile("[0-9][.][0-9]{1,2}[.][0-9]{1,2}")
    print(version)
    assert version_regex.match(version)


def test_get_image_lib_versions():
    data = ocr.tesseractwrap.get_image_lib_versions()
    assert isinstance(data, str)


def test_get_image_lib_versions_dict():
    data = ocr.image_lib_versions()
    assert isinstance(data, dict)

def test_get_tesseract_version():
    data = ocr.tesseractwrap.tesseract_version()
    print(data)
    assert isinstance(data, str)

