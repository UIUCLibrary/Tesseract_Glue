
from conan import ConanFile


class Exiv2BindConan(ConanFile):
    requires = [
        "tesseract/4.1.1@#d816dfa99a51974f851f579b1b384e21",
        "leptonica/1.82.0@#acb0265f3ffe6f0517a344920ef661ca",
        "zlib/1.3.1",
    ]
    settings = "os", "arch", "compiler", "build_type"

    generators = ["json", "cmake_paths"]
    default_options = {}

    def imports(self):
        self.copy("*.dll", dst=".", src="bin")
        self.copy("*.dylib*", dst=".", src="lib")  # From lib to bin
        self.copy("libtiffxx.5.dylib", dst=".", src="lib")  # From lib to bin
        self.copy("libtiff.5.dylib", dst=".", src="lib")  # From lib to bin
        self.copy("libtiff.so.*", src="lib")
        self.copy("libtiff.so", src="lib")
        self.copy("libtiffxx.so", src="lib")
        self.copy("libtiffxx.so.*", src="lib")
        self.copy("libiconv.so", src="lib")
        self.copy("libiconv.so.*", src="lib")
        self.copy("libcharset.so", src="lib")
        self.copy("libcharset.so.*", src="lib")
        self.copy("tesseract", dst="", src="bin", keep_path=True)
    def configure(self):
        if self.settings.os == "Windows":
            self.options['leptonica'].shared = True
