import os
import shutil
import urllib.request
from tempfile import TemporaryDirectory
from download_sample_files import download_sample_files, validate_file, get_sample_image_metadata

import pytest

TESSDATA_SOURCE_URL = "https://github.com/tesseract-ocr/tessdata/raw/main/"
SAMPLES_CSV_FILE =os.path.join(os.path.dirname(__file__), "samplefiles.csv")


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
    expected_files =[
        "eng.traineddata",
        "osd.traineddata"
    ]
    if tessdata_path := os.getenv("TESSDATA_PREFIX"):
        for file in expected_files:
            if not os.path.exists(os.path.join(tessdata_path, file)):
                raise FileNotFoundError(f"Expected file is missing from TESSDATA_PREFIX: {file}")
        return tessdata_path
    english_data_url = "{}{}".format(TESSDATA_SOURCE_URL, "eng.traineddata")
    osd_data_url = "{}{}".format(TESSDATA_SOURCE_URL, "osd.traineddata")
    test_path = tmpdir_factory.mktemp("data", numbered=False)
    tessdata_path = os.path.join(test_path, "tessdata")

    if not os.path.exists(tessdata_path):
        os.makedirs(tessdata_path)
    download_data(osd_data_url, destination=tessdata_path)
    download_data(english_data_url, destination=tessdata_path)

    return tessdata_path


def use_existing_sample_data(sample_images_path):
    if not os.path.exists(sample_images_path):
        raise FileNotFoundError(f"provided sample path does not exist: {sample_images_path}")

    test_images_data = get_sample_image_metadata(
        os.path.join(os.path.dirname(__file__), "samplefiles.csv")
    )
    for file_record in test_images_data:
        file = file_record["file"]
        expected_path = os.path.join(sample_images_path, file)
        if not os.path.exists(expected_path):
            raise FileNotFoundError(f"expected test file is missing from \"{sample_images_path}\": {file}")
        if not validate_file(os.path.join(sample_images_path, file), file_record["sha256"]):
            raise ValueError("Expected hash value does not match")
    return sample_images_path

def use_sample_files_from_download(tmp_path):
    sample_images_path = os.path.join(tmp_path, "sample_images")
    download_sample_files(sample_images_path, SAMPLES_CSV_FILE)
    return sample_images_path


@pytest.fixture(scope="session", autouse=True)
def sample_images(tmpdir_factory):
    if sample_images_path := os.getenv("SAMPLES_PATH"):
        yield use_existing_sample_data(sample_images_path)
    else:
        yield use_sample_files_from_download(
            tmp_path=tmpdir_factory.mktemp("sample_files_data", numbered=False)
        )
