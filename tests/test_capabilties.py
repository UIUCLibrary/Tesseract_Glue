import pytest

from uiucprescon import ocr


@pytest.fixture
def linked_image_libs():
    return ocr.image_lib_versions()


@pytest.mark.parametrize("library_name", ['libopenjp2', 'libtiff'])
def test_expected_decoders(linked_image_libs, library_name):
    assert library_name in linked_image_libs, f"{library_name} not in {', '.join(linked_image_libs.keys())}"

@pytest.mark.parametrize(
    "data_string, parsed_data",
    [
        (
            "libgif 5.2.1 : libjpeg 9f : libpng 1.6.50 : libtiff 4.6.0 : zlib 1.3.1 : libwebp 1.6.0 : libopenjp2 2.5.2",
            {
                "libgif": "5.2.1",
                "libjpeg": "9f",
                "libpng": "1.6.50",
                "libtiff": "4.6.0",
                "libopenjp2": "2.5.2",
                "libwebp": "1.6.0",
                "zlib": "1.3.1",
            }
        ),
        (
            "libgif 6.1.3 : libjpeg 9f (libjpeg-turbo 3.2.0) : libpng 1.6.50 : libtiff 4.6.0 : zlib 1.3.1 : libwebp 1.6.0 : libopenjp2 2.5.2",
            {
                "libgif": "6.1.3",
                "libjpeg": "9f (libjpeg-turbo 3.2.0)",
                "libpng": "1.6.50",
                "libtiff": "4.6.0",
                "zlib": "1.3.1",
                "libwebp": "1.6.0",
                "libopenjp2": "2.5.2",
            }
        )
    ]
)
def test_parse_version(data_string, parsed_data):
    # string = "libgif 6.1.3 : libjpeg 9f (libjpeg-turbo 3.2.0) : libpng 1.6.50 : libtiff 4.6.0 : zlib 1.3.1 : libwebp 1.6.0 : libopenjp2 2.5.2"
    assert ocr.capabilities.parse_version(data_string) == parsed_data