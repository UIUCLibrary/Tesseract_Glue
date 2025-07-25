
from conan import ConanFile


class TesseractBindConan(ConanFile):
    requires = [
        "tesseract/5.2.0",
        "leptonica/1.83.1"
    ]
    settings = "os", "arch", "compiler", "build_type"
    generators = ["CMakeToolchain", "CMakeDeps"]

    default_options = {
        "tesseract/*:with_libcurl": False
    }

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
