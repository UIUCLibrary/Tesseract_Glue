import os
import sys
from distutils import ccompiler
from pathlib import Path

import setuptools
import shutil
from distutils.version import StrictVersion

sys.path.insert(0, os.path.dirname(__file__))
from builders.deps import get_win_deps

cmd_class = {}
try:
    from builders import conan_libs
    cmd_class["build_conan"] = conan_libs.BuildConan
except ImportError:
    pass

try:
    from builders.pybind11_builder import BuildPybind11Extension


    def test_tesseract(build_file: str):
        with open(build_file, "r") as f:
            parser = conan_libs.ConanBuildInfoParser(f)
            data = parser.parse()
        path = data['bindirs_tesseract']
        tesseract = shutil.which("tesseract", path=path[0])

        tester = {
            'darwin': conan_libs.MacResultTester,
            'linux': conan_libs.LinuxResultTester,
            'win32': conan_libs.WindowsResultTester
        }.get(sys.platform)

        if tester is None:
            raise AttributeError(f"unable to test for platform {sys.platform}")

        compiler = ccompiler.new_compiler()
        tester = tester(compiler)
        libs_dirs = data['libdirs']
        for libs_dir in libs_dirs:
            tester.test_shared_libs(libs_dir)
        tester.test_binary_dependents(Path(tesseract))
        print("Testing Tesseract exec")
        compiler.spawn([tesseract, '--version'])
        print("Testing Tesseract exec - Done")


    class BuildTesseractExt(BuildPybind11Extension):

        def build_extension(self, ext):
            missing = self.find_missing_libraries(ext)

            if len(missing) > 0:
                self.announce(f"missing required deps [{', '.join(missing)}]. "
                              f"Trying to get them with conan", 5)
                self.run_command("build_conan")

            # This test os needed because the conan version keeps silently
            # breaking the linking to openjp2 library.
            conanfileinfo_locations = [
                self.build_temp
            ]
            conan_info_dir = os.environ.get('CONAN_BUILD_INFO_DIR')
            if conan_info_dir:
                conanfileinfo_locations.insert(0, conan_info_dir)
            for location in conanfileinfo_locations:
                conanbuildinfo = os.path.join(location, "conanbuildinfo.txt")
                if os.path.exists(conanbuildinfo):
                    test_tesseract(conanbuildinfo)
                    break
            super().build_extension(ext)

        def run(self):
            pybind11_include_path = self.get_pybind11_include_path()

            if pybind11_include_path is None:
                raise FileNotFoundError("Missing pybind11 include path")

            self.include_dirs.append(pybind11_include_path)
            super().run()

            for e in self.extensions:

                dll_name = \
                    os.path.join(self.build_lib, self.get_ext_filename(e.name))

                output_file = os.path.join(self.build_temp, f'{e.name}.dependents')
                if self.compiler.compiler_type != "unix":
                    if not self.compiler.initialized:
                        self.compiler.initialize()
                    deps = get_win_deps(dll_name, output_file, compiler=self.compiler)
                    dest = os.path.dirname(dll_name)

                    for dep in deps:
                        dll = self.find_deps(dep)
                        if dll is None:
                            raise FileNotFoundError(f"Missing for {dep}")
                        shutil.copy(dll, dest)

    cmd_class["build_ext"] = BuildTesseractExt
except ImportError as e:
    pass

PACKAGE_NAME = "uiucprescon.ocr"

if StrictVersion(setuptools.__version__) < StrictVersion('30.3'):
    print('your setuptools version does not support using setup.cfg. '
          'Upgrade setuptools and repeat the installation.',
          file=sys.stderr
          )

    sys.exit(1)

tesseract_extension = setuptools.Extension(
    "uiucprescon.ocr.tesseractwrap",
    sources=[
        'uiucprescon/ocr/Capabilities.cpp',
        'uiucprescon/ocr/glue.cpp',
        'uiucprescon/ocr/reader.cpp',
        'uiucprescon/ocr/reader2.cpp',
        'uiucprescon/ocr/tesseractwrap.cpp',
        'uiucprescon/ocr/Image.cpp',
        'uiucprescon/ocr/ImageLoaderStrategies.cpp',
        'uiucprescon/ocr/fileLoader.cpp',
        'uiucprescon/ocr/glueExceptions.cpp',
        'uiucprescon/ocr/utils.cpp',
    ],
    libraries=[
        'leptonica',
        "tesseract",
    ],
    language='c++',


)

tesseract_extension.cmake_source_dir = \
    os.path.abspath(os.path.dirname(__file__))

setuptools.setup(
    packages=['uiucprescon.ocr'],
    setup_requires=[
        'pytest-runner',
    ],
    install_requires=[],
    test_suite='tests',
    tests_require=[
        'pytest',
        'pytest-bdd'
    ],
    namespace_packages=["uiucprescon"],
    ext_modules=[
        tesseract_extension
    ],
    package_data={"uiucprescon.ocr": ["py.typed"]},
    cmdclass=cmd_class,
)
