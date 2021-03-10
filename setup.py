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

    from setuptools.command.build_ext import build_ext
    # class BuildPybind11Extension(build_ext):
    #     user_options = build_ext.user_options + [
    #         ('pybind11-url=', None,
    #          "Url to download Pybind11")
    #     ]
    #
    #     def initialize_options(self):
    #         super().initialize_options()
    #         self.pybind11_url = None
    #
    #     def finalize_options(self):
    #         PYBIND11_DEFAULT_URL = \
    #             "https://github.com/pybind/pybind11/archive/v2.5.0.tar.gz"
    #         self.pybind11_url = self.pybind11_url or PYBIND11_DEFAULT_URL
    #         super().finalize_options()
    #
    #     def find_deps(self, lib, search_paths=None):
    #         search_paths = search_paths or os.environ['path'].split(";")
    #
    #         search_paths.append(
    #             self.get_finalized_command("build_clib").build_temp
    #         )
    #
    #         for path in search_paths:
    #             if not os.path.exists(path):
    #                 self.announce(f"Skipping invalid path: {path}", 5)
    #                 continue
    #             for f in os.scandir(path):
    #                 if f.name.lower() == lib.lower():
    #                     return f.path
    #
    #     def find_missing_libraries(self, ext):
    #         missing_libs = []
    #         for lib in ext.libraries:
    #             if self.compiler.find_library_file(self.library_dirs + ext.library_dirs, lib) is None:
    #                 missing_libs.append(lib)
    #         return missing_libs
    #
    #     def build_extension(self, ext):
    #         if self.compiler.compiler_type == "unix":
    #             ext.extra_compile_args.append("-std=c++14")
    #         else:
    #             ext.extra_compile_args.append("/std:c++14")
    #             # ext.libraries.append("Shell32")
    #         missing = self.find_missing_libraries(ext)
    #
    #         if len(missing) > 0:
    #             self.announce(f"missing required deps [{', '.join(missing)}]. "
    #                           f"Trying to get them with conan", 5)
    #             self.run_command("build_conan")
    #         super().build_extension(ext)
    #
    #     def get_pybind11_include_path(self):
    #         import tarfile
    #         from urllib import request
    #         pybind11_archive_filename = os.path.split(self.pybind11_url)[1]
    #
    #         pybind11_archive_downloaded = os.path.join(self.build_temp,
    #                                                    pybind11_archive_filename)
    #
    #         pybind11_source = os.path.join(self.build_temp, "pybind11")
    #         if not os.path.exists(self.build_temp):
    #             os.makedirs(self.build_temp)
    #
    #         if not os.path.exists(pybind11_source):
    #             if not os.path.exists(pybind11_archive_downloaded):
    #                 self.announce("Downloading pybind11", level=5)
    #                 request.urlretrieve(
    #                     self.pybind11_url, filename=pybind11_archive_downloaded)
    #                 self.announce("pybind11 Downloaded", level=5)
    #             with tarfile.open(pybind11_archive_downloaded, "r") as tf:
    #                 for f in tf:
    #                     if "pybind11.h" in f.name:
    #                         self.announce("Extract pybind11.h to include path")
    #
    #                     tf.extract(f, pybind11_source)
    #         for root, dirs, files in os.walk(pybind11_source):
    #             for f in files:
    #                 if f == "pybind11.h":
    #                     return os.path.relpath(
    #                         os.path.join(root, ".."),
    #                         os.path.dirname(__file__)
    #                     )
    class BuildTesseractExt(BuildPybind11Extension):

        def build_extension(self, ext):
            super().build_extension(ext)

        def run(self):
            pybind11_include_path = self.get_pybind11_include_path()

            if pybind11_include_path is not None:
                self.include_dirs.append(pybind11_include_path)

            super().run()
            for e in self.extensions:
                dll_name = \
                    os.path.join(self.build_lib, self.get_ext_filename(e.name))

                output_file = os.path.join(self.build_temp, f'{e.name}.dependents')
                if self.compiler.compiler_type != "unix":
                    if not self.compiler.initialized:
                        self.compiler.initialize()
                    deps = get_win_deps(dll_name, output_file,
                                        compiler=self.compiler)
                    dest = os.path.dirname(dll_name)

                    for dep in deps:
                        dll = self.find_deps(dep)
                        if dll is None:
                            raise FileNotFoundError("Mising for {}".format(dep))
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
        "tesseract",
    ],
    # define_macros=[
    #     ("OPJ_STATIC",),
    #     ("LZMA_API_STATIC",),
    #     ("LIBJPEG_STATIC",)
    # ],
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
    cmdclass=cmd_class
)
