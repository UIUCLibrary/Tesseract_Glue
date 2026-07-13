
from conan import ConanFile

required_conan_version='>=2.28'

class TesseractBindConan(ConanFile):
    requires = [
        "tesseract/5.5.2",
        "leptonica/1.87.0"
    ]
    settings = "os", "arch", "compiler", "build_type"
    generators = ["CMakeToolchain", "CMakeDeps"]


    def build_requirements(self):
        self.test_requires('catch2/3.11.0')

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
