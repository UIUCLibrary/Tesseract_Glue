
from conan import ConanFile


class Exiv2BindConan(ConanFile):
    requires = [
        "tesseract/4.1.1",
        "zlib/1.2.13",
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

