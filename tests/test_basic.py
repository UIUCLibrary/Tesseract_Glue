import re

from uiucprescon import ocr
import types


def test_import_module():
    assert isinstance(ocr, types.ModuleType)


def test_version():

    e = ocr.Engine("")
    version = e.get_version()
    version_regex = re.compile("[0-9][.][0-9]{1,2}[.][0-9]{1,2}")
    print(version)
    assert version_regex.match(version)

