import os
import sys
from distutils import ccompiler
from pathlib import Path
from pprint import pprint

import setuptools
import shutil
from distutils.version import StrictVersion

from pybind11.setup_helpers import Pybind11Extension
from uiucprescon.build import conan_libs
from uiucprescon.build.pybind11_builder import BuildPybind11Extension, UseSetuptoolsCompilerFileLibrary

PACKAGE_NAME = "uiucprescon.ocr"

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


class BuildTesseractExt(BuildPybind11Extension):

    def build_extension(self, ext: Pybind11Extension):
        missing = self.find_missing_libraries(ext, strategies=[
            UseSetuptoolsCompilerFileLibrary(
                compiler=self.compiler,
                dirs=self.library_dirs + ext.library_dirs
            ),
        ])
        build_conan = self.get_finalized_command("build_conan")
        if len(missing) > 0:
            self.announce(f"missing required deps [{', '.join(missing)}]. "
                          f"Trying to get them with conan", 5)
            build_conan.build_libs = ['outdated']
        else:
            build_conan.build_libs = []
        build_conan.run()
        # This test os needed because the conan version keeps silently
        # breaking the linking to openjp2 library.
        build_clib = self.get_finalized_command("build_clib")
        conanfileinfo_locations = [
            self.build_temp,
            os.path.join(self.build_temp, "Release"),
            os.path.join(build_clib.build_temp, "conan"),
        ]
        conan_info_dir = os.environ.get('CONAN_BUILD_INFO_DIR')
        if conan_info_dir is not None:
            conanfileinfo_locations.insert(0, conan_info_dir)
        for location in conanfileinfo_locations:
            conanbuildinfo = os.path.join(location, "conanbuildinfo.txt")
            if os.path.exists(conanbuildinfo):
                test_tesseract(conanbuildinfo)
                break
        else:
            raise FileNotFoundError(
                f"Missing file conanbuildinfo.txt. "
                f"Searched locations {*conanfileinfo_locations,}"
            )
        self.announce(f"Using data from {conanbuildinfo}", level=5)
        try:
            super().build_extension(ext)
        except Exception:
            pprint(ext.__dict__)
            raise
        tester = {
            'darwin': conan_libs.MacResultTester,
            'linux': conan_libs.LinuxResultTester,
            'win32': conan_libs.WindowsResultTester
        }.get(sys.platform)
        dll_name = \
            os.path.join(self.build_lib, self.get_ext_filename(ext.name))

        tester().test_binary_dependents(Path(dll_name))

    def run(self):
        from uiucprescon.build.deps import get_win_deps
        super().run()
        def locate(dep, location):
            for f in os.scandir(dest):
                if f.name.lower() == dep.lower():
                    return f.path

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
                    if os.path.exists(os.path.join(dest, dep)):
                        print(f"Package already has {dep}")
                        continue
                    paths = os.environ['path'].split(";")
                    dll = self.find_deps(dep, paths)
                    if dll is None:
                        for i in os.scandir(dest):
                            print(i.path)
                        raise FileNotFoundError(f"Missing {dep}. Searched {paths}")
                    shutil.copy(dll, dest)



if StrictVersion(setuptools.__version__) < StrictVersion('30.3'):
    print('your setuptools version does not support using setup.cfg. '
          'Upgrade setuptools and repeat the installation.',
          file=sys.stderr
          )

    sys.exit(1)
tesseract_extension = Pybind11Extension(
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
    cxx_std=14
)

tesseract_extension.cmake_source_dir = \
    os.path.abspath(os.path.dirname(__file__))

setuptools.setup(
    ext_modules=[
        tesseract_extension
    ],
    cmdclass={
        "build_ext": BuildTesseractExt,
        "build_conan": conan_libs.BuildConan
    }
)
