import os
import shutil
import urllib.request
from tempfile import TemporaryDirectory

import pytest

USER_CONTENT_URL = "https://jenkins.library.illinois.edu/nexus/repository/sample-data/ocr_test_images"
TESSDATA_SOURCE_URL = "https://github.com/tesseract-ocr/tessdata/raw/4.0.0/"


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--integration"):
        # --integration given in cli: do not skip integration tests
        return

    skip_integration = pytest.mark.skip(
        reason="skipped integration tests. Use --integration option to run")

    for item in items:
        if "integration" in item.keywords or "expensive" in item.keywords :
            item.add_marker(skip_integration)


def download_data(url, destination):
    base_name = os.path.basename(url)
    destination_file = os.path.join(destination, base_name)
    if os.path.exists(destination_file):
        return

    with TemporaryDirectory() as download_path:

        # if not os.path.exists()
        print("Downloading {}".format(url))
        test_file_path = os.path.join(download_path, base_name)

        urllib.request.urlretrieve(url, filename=test_file_path)
        if not os.path.exists(test_file_path):
            raise FileNotFoundError(
                "Failure to download file from {}".format(url))

        shutil.move(test_file_path, destination)

        print("{} successfully downloaded".format(
            os.path.split(test_file_path)[-1]))


@pytest.fixture(scope="session", autouse=True)
def tessdata_eng(tmpdir_factory):

    english_data_url = "{}{}".format(TESSDATA_SOURCE_URL, "eng.traineddata")
    osd_data_url = "{}{}".format(TESSDATA_SOURCE_URL, "osd.traineddata")
    test_path = tmpdir_factory.mktemp("data", numbered=False)
    tessdata_path = os.path.join(test_path, "tessdata")

    if not os.path.exists(tessdata_path):
        os.makedirs(tessdata_path)
    download_data(osd_data_url, destination=tessdata_path)
    download_data(english_data_url, destination=tessdata_path)

    return tessdata_path


@pytest.fixture(scope="session", autouse=True)
def sample_images(tmpdir_factory):

    test_images = [
        "IlliniLore_1944_00000011.tif"
    ]

    test_path = tmpdir_factory.mktemp("sample_files_data", numbered=False)
    sample_images_path = os.path.join(test_path, "sample_images")
    if not os.path.exists(sample_images_path):
        os.makedirs(sample_images_path)
    for test_image in test_images:
        url = "{}/{}".format(USER_CONTENT_URL, test_image)

        download_data(url, destination=sample_images_path)

    yield sample_images_path
    shutil.rmtree(test_path)
