import os
import sys

import setuptools
import shutil
from distutils.version import StrictVersion

sys.path.insert(0, os.path.dirname(__file__))
from builders.deps import get_win_deps

cmd_class = {}
try:
    from builders.conan import BuildConan
    cmd_class["build_conan"] = BuildConan
except ImportError:
    pass

try:
    from builders.pybind11_builder import BuildPybind11Extension

    class BuildTesseractExt(BuildPybind11Extension):

        def build_extension(self, ext):
            missing = self.find_missing_libraries(ext)

            if len(missing) > 0:
                self.announce(f"missing required deps [{', '.join(missing)}]. "
                              f"Trying to get them with conan", 5)
                self.run_command("build_conan")
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
                            raise FileNotFoundError("Missing for {}".format(dep))
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
        'pybind11>=2.5'
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
    cmdclass=cmd_class,
)
