import re

from uiucprescon import ocr
import types
import pytest

def test_import_module():
    assert isinstance(ocr, types.ModuleType)


def test_version(record_property):

    e = ocr.Engine("")
    version = e.get_version()
    version_regex = re.compile("[0-9][.][0-9]{1,2}[.][0-9]{1,2}")
    record_property("version", version)
    assert version_regex.match(version)


def test_get_image_lib_versions(record_property):
    data = ocr.tesseractwrap.get_image_lib_versions()
    record_property("lib_versions", data)
    assert isinstance(data, str)



def test_get_tesseract_version(record_property):
    data = ocr.tesseractwrap.tesseract_version()
    record_property("tesseract_version", data)
    assert isinstance(data, str)

