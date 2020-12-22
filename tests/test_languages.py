import os
from unittest.mock import Mock

from uiucprescon import ocr
import urllib.request


def test_download_languague_downloads_file(monkeypatch, tmpdir):

    def mocked_function(*args, **kwargs):
        m = Mock()
        m.read = Mock(return_value=None)
        return m

    temp_path = str(tmpdir)
    monkeypatch.setattr(urllib.request, "urlopen", mocked_function)
    ocr.languages._download_languague("www.fake.com/eng.tessdata", temp_path)

    assert os.path.exists(os.path.join(temp_path, 'eng.tessdata'))

