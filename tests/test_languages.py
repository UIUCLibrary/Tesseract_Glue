import os
from unittest.mock import Mock, MagicMock, create_autospec

from uiucprescon import ocr
import urllib.request


def test_download_languague_downloads_file(monkeypatch, tmpdir):
    dummy_data = iter([
        b"1234555",
        b"7890312",
        None
    ])
    m = MagicMock()

    m.read = Mock(side_effect=dummy_data)

    def mocked_function(*args, **kwargs):
        return m

    temp_path = str(tmpdir)
    monkeypatch.setattr(urllib.request, "urlopen", mocked_function)
    ocr.languages._download_languague("www.fake.com/eng.tessdata", temp_path)

    assert os.path.exists(os.path.join(temp_path, 'eng.tessdata'))

