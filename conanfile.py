
from conan import ConanFile


class Exiv2BindConan(ConanFile):
    requires = [
        "tesseract/4.1.1",
    ]
    settings = "os", "arch", "compiler", "build_type"

    generators = ["json", "cmake_paths"]
    default_options = {}

    def imports(self):
        self.copy("*.dll", dst=".", src="bin")  # From bin to bin
        self.copy("libtiff.so.*", dst="lib", src="lib")  # From bin to bin
        self.copy("libtiff.so", dst="lib", src="lib")  # From bin to bin
        self.copy("libiconv.so", dst="lib", src="lib")  # From bin to bin
        self.copy("libiconv.so.*", dst="lib", src="lib")  # From bin to bin
        self.copy("libcharset.so", dst="lib", src="lib")  # From bin to bin
        self.copy("libcharset.so.*", dst="lib", src="lib")  # From bin to bin
        self.copy("tesseract", dst="", src="bin", keep_path=True)  # From bin to bin

    def configure(self):
        if self.settings.os == "Linux":
            self.options["libtiff"].shared = True
            self.options["libiconv"].shared = True
