import os

from conans import ConanFile, CMake

class Exiv2BindConan(ConanFile):
    requires = [
        "tesseract/4.1.1",
    ]
    settings = "os", "arch", "compiler", "build_type"

    generators = ["json"]
    default_options = {}
