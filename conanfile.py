import os

from conans import ConanFile, CMake

class Exiv2BindConan(ConanFile):
    requires = [
        "tesseract/4.1.1",
    ]
    settings = "os", "arch", "compiler", "build_type"

    generators = ["json"]
    default_options = {}

    def configure(self):
        if self.settings.os == "Windows":
            self.options['libarchive'].shared = True
        # super().configure()

    def imports(self):
        self.copy("*.dll", dst=".", src="bin")  # From bin to bin