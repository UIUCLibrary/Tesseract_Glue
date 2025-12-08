
from conan import ConanFile


class TesseractBindConan(ConanFile):
    requires = [
        "tesseract/5.5.1",
        "leptonica/1.83.1"
    ]
    settings = "os", "arch", "compiler", "build_type"
    generators = ["CMakeToolchain", "CMakeDeps"]


    def build_requirements(self):
        self.test_requires('catch2/3.11.0')

    def requirements(self):
        self.requires("libjpeg/9f", override=True)

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
