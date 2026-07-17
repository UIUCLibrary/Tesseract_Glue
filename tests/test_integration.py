import os
import shutil
import urllib.request
from tempfile import TemporaryDirectory
import pathlib

import pytest
from pypdf import PdfReader

from uiucprescon import ocr


TESSDATA_SOURCE_URL_BASE = "https://raw.githubusercontent.com/tesseract-ocr/tessdata"


def download_data(url, destination):
    with TemporaryDirectory() as download_path:
        base_name = os.path.basename(url)
        destination_file = os.path.join(destination, base_name)

        if os.path.exists(destination_file):
            return

        # if not os.path.exists()
        print("Downloading {}".format(url))
        test_file_path = os.path.join(download_path, base_name)

        urllib.request.urlretrieve(url, filename=test_file_path)
        if not os.path.exists(test_file_path):
            raise FileNotFoundError(
                "Failure to download file from {}".format(url))

        shutil.move(test_file_path, destination)


@pytest.mark.integration
def test_reader_with_data(tessdata_eng, sample_images):
    reader = ocr.Reader(language_code="eng", tesseract_data_path=tessdata_eng)
    test_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")

    text = reader.read(test_image)
    assert isinstance(text, str)

#
# @pytest.mark.integration
# def test_no_osd_file(tmpdir_factory):
#     e = ocr.Engine("")
#     version = e.get_version()
#     english_data_url = "{}/{}/{}".format(TESSDATA_SOURCE_URL_BASE, "4.0.0", "eng.traineddata")
#     expected_files = ["eng.traineddata"]
#     if tessdata_path := os.getenv("TESSDATA_PREFIX"):
#         for file in expected_files:
#             if not os.path.exists(os.path.join(tessdata_path, file)):
#                 raise FileNotFoundError(f"Expected file is missing from TESSDATA_PREFIX: {file}")
#     else:
#         tessdata_path = tmpdir_factory.mktemp("no_osd_tessdata", numbered=False)
#
#         if not os.path.exists(tessdata_path):
#             os.makedirs(tessdata_path)
#         download_data(english_data_url, destination=tessdata_path)
#     with pytest.raises(FileNotFoundError):
#
#         reader = ocr.Reader(
#             language_code="eng",
#             tesseract_data_path=tessdata_path
#         )
#     shutil.rmtree(tessdata_path)
#
# #
# @pytest.mark.expensive
# def test_download_language_pack():
#     with TemporaryDirectory() as download_path:
#         print(download_path)
#         extract_path = os.path.join(download_path, "extracted")
#
#         if not os.path.exists(extract_path):
#             os.mkdir(extract_path)
#
#         ocr.languages.download_language_pack(
#             "4.0.0",
#             destination=download_path,
#             md5_hash="78d0e9da53d29277c0b28c2dc2ead4f9"
#         )
#         expect_file = os.path.join(download_path, "4.0.0")
#         assert os.path.exists(expect_file)

@pytest.mark.integration
def test_create_pdf(tessdata_eng, sample_images, tmpdir):
    api = ocr.OCRApi(datapath=tessdata_eng, language_code="eng")
    assert pathlib.Path(api.datapath) == pathlib.Path(tessdata_eng)
    assert os.path.exists(api.datapath)
    output_pdf =  tmpdir / "output.pdf"
    test_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
    ocr.create_pdf([test_image], str(output_pdf), api)
    assert  os.path.exists(str(output_pdf))

@pytest.mark.integration
def test_create_pdf_invalid_file(tessdata_eng, sample_images, tmpdir):
    output_pdf =  str(tmpdir / "output.pdf")
    test_image = os.path.join(sample_images, "not_a_real_file.tif")
    api = ocr.OCRApi(datapath=tessdata_eng, language_code="eng")
    with pytest.raises(ocr.tesseractwrap.TesseractGlueException) as e:
        ocr.create_pdf([test_image], output_pdf, api)
    assert "Unable to load" in str(e)

class TestOCRApi:
    @pytest.mark.integration
    def test_datapath(self, tessdata_eng):
        api = ocr.OCRApi(datapath=tessdata_eng, language_code="eng")
        assert pathlib.Path(api.datapath) == pathlib.Path(tessdata_eng)

class TestPDFBuilder:

    @pytest.mark.integration
    def test_open_close(self, tessdata_eng, sample_images, tmpdir):
        output_pdf =  tmpdir / "output.pdf"
        api = ocr.OCRApi(datapath=tessdata_eng, language_code="eng")
        builder = ocr.PDFBuilder(str(output_pdf), api)
        builder.open()
        test_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
        builder.add_page(test_image)
        builder.close()
        assert os.path.exists(str(output_pdf))

    @pytest.mark.integration
    def test_context_manager(self, tessdata_eng, sample_images, tmpdir):
        output_pdf =  tmpdir / "output.pdf"
        api = ocr.OCRApi(datapath=tessdata_eng, language_code="eng")
        with ocr.PDFBuilder(
            str(output_pdf),
            api
        ) as builder:
            builder.add_page(
                os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
            )
        assert os.path.exists(str(output_pdf))
    @pytest.fixture(scope="package")
    def generated_pdf(self, tessdata_eng, sample_images, tmp_path_factory):
        test_path = tmp_path_factory.mktemp("test_path")
        output_pdf =  test_path / "output.pdf"
        api = ocr.OCRApi(datapath=tessdata_eng, language_code="eng")
        with ocr.PDFBuilder(
            str(output_pdf),
            api,
        ) as builder:
            builder.add_page(
                os.path.join(sample_images, "IlliniLore_1944_00000011.tif")
            )
        return str(output_pdf)

    @pytest.mark.integration
    def test_pages(self, generated_pdf):
        reader = PdfReader(generated_pdf)
        text = reader.pages[0].extract_text()
        assert text.startswith("Founders’ Day")

    @pytest.mark.integration
    def test_page_count(self, generated_pdf):
        reader = PdfReader(generated_pdf)
        assert len(reader.pages) > 0
    @pytest.mark.integration
    def test_exists(self, generated_pdf):
        assert os.path.exists(generated_pdf)
