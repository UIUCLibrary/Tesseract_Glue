import subprocess
import json
import setuptools
from setuptools.command.build_ext import build_ext
import shutil
import os
import sys
import re
from distutils.version import StrictVersion
from typing import List
import tarfile
from urllib import request

DEPS_REGEX = \
    r'(?<=(Image has the following dependencies:(\n){2}))((?<=\s).*\.dll\n)*'

PACKAGE_NAME = "uiucprescon.ocr"
PYBIND11_DEFAULT_URL = \
    "https://github.com/pybind/pybind11/archive/v2.5.0.tar.gz"


if StrictVersion(setuptools.__version__) < StrictVersion('30.3'):
    print('your setuptools version does not support using setup.cfg. '
          'Upgrade setuptools and repeat the installation.',
          file=sys.stderr
          )

    sys.exit(1)


def parse_dumpbin_deps(file) -> List[str]:

    dlls = []
    dep_regex = re.compile(DEPS_REGEX)

    with open(file) as f:
        d = dep_regex.search(f.read())
        for x in d.group(0).split("\n"):
            if x.strip() == "":
                continue
            dll = x.strip()
            dlls.append(dll)
    return dlls


def remove_system_dlls(dlls):
    non_system_dlls = []
    for dll in dlls:
        if dll.startswith("api-ms-win-crt"):
            continue

        if dll.startswith("python"):
            continue

        if dll == "KERNEL32.dll":
            continue
        non_system_dlls.append(dll)
    return non_system_dlls


class BuildTesseractExt(build_ext):
    user_options = build_ext.user_options + [
        ('pybind11-url=', None,
         "Url to download Pybind11")
    ]

    def initialize_options(self):
        super().initialize_options()
        self.pybind11_url = None

    def finalize_options(self):
        self.pybind11_url = self.pybind11_url or PYBIND11_DEFAULT_URL
        super().finalize_options()

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
                self.compiler.spawn(
                    [
                        'dumpbin',
                        '/dependents',
                        dll_name,
                        f'/out:{output_file}'
                    ]
                )
                deps = parse_dumpbin_deps(file=output_file)
                deps = remove_system_dlls(deps)
                dest = os.path.dirname(dll_name)

                for dep in deps:
                    dll = self.find_deps(dep)
                    shutil.copy(dll, dest)

    def find_deps(self, lib, search_paths=None):
        search_paths = search_paths or os.environ['path'].split(";")
        for path in search_paths:
            if not os.path.exists(path):
                self.announce(f"Skipping invalid path: {path}", 5)
                continue
            for f in os.scandir(path):
                if f.name.lower() == lib.lower():
                    return f.path

    def find_missing_libraries(self, ext):
        missing_libs = []
        for lib in ext.libraries:
            if self.compiler.find_library_file(self.library_dirs + ext.library_dirs, lib) is None:
                missing_libs.append(lib)
        return missing_libs

    def build_extension(self, ext):
        if self.compiler.compiler_type == "unix":
            ext.extra_compile_args.append("-std=c++14")
        else:
            ext.extra_compile_args.append("/std:c++14")
            # ext.libraries.append("Shell32")

        missing = self.find_missing_libraries(ext)

        if len(missing) > 0:
            self.announce(f"missing required deps [{', '.join(missing)}]. "
                          f"Trying to get them with conan", 5)
            self.run_command("build_conan")
        super().build_extension(ext)

    def get_pybind11_include_path(self):
        pybind11_archive_filename = os.path.split(self.pybind11_url)[1]

        pybind11_archive_downloaded = os.path.join(self.build_temp,
                                                   pybind11_archive_filename)

        pybind11_source = os.path.join(self.build_temp, "pybind11")
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        if not os.path.exists(pybind11_source):
            if not os.path.exists(pybind11_archive_downloaded):
                self.announce("Downloading pybind11", level=5)
                request.urlretrieve(
                    self.pybind11_url, filename=pybind11_archive_downloaded)
                self.announce("pybind11 Downloaded", level=5)
            with tarfile.open(pybind11_archive_downloaded, "r") as tf:
                for f in tf:
                    if "pybind11.h" in f.name:
                        self.announce("Extract pybind11.h to include path")

                    tf.extract(f, pybind11_source)
        for root, dirs, files in os.walk(pybind11_source):
            for f in files:
                if f == "pybind11.h":
                    return os.path.relpath(
                        os.path.join(root, ".."),
                        os.path.dirname(__file__)
                    )


tesseract_extension = setuptools.Extension(
    "uiucprescon.ocr.tesseractwrap",
    sources=[
        'uiucprescon/ocr/glue.cpp',
        'uiucprescon/ocr/reader.cpp',
        'uiucprescon/ocr/reader2.cpp',
        'uiucprescon/ocr/tesseractwrap.cpp',
        'uiucprescon/ocr/utils.cpp',
    ],
    libraries=[
        "tesseract",
    ],
    language='c++',
)

tesseract_extension.cmake_source_dir = \
    os.path.abspath(os.path.dirname(__file__))


class BuildConan(setuptools.Command):
    user_options = [
        ('conan-exec=', "c", 'conan executable')
    ]

    description = "Get the required dependencies from a Conan package manager"

    def initialize_options(self):
        self.conan_exec = None

    def finalize_options(self):
        if self.conan_exec is None:
            self.conan_exec = shutil.which("conan")
            if self.conan_exec is None:
                raise Exception("missing conan_exec")

    def getConanBuildInfo(self, root_dir):
        for root, dirs, files in os.walk(root_dir):
            for f in files:
                if f == "conanbuildinfo.json":
                    return os.path.join(root, f)
        return None

    def run(self):
        build_ext_cmd = self.get_finalized_command("build_ext")
        build_dir = build_ext_cmd.build_temp
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
        build_dir_full_path = os.path.abspath(build_dir)
        install_command = [
            self.conan_exec,
            "install",
            "--build",
            "missing",
            "-if", build_dir_full_path,
            os.path.abspath(os.path.dirname(__file__))
        ]

        subprocess.check_call(install_command, cwd=build_dir)

        conanbuildinfo_file = self.getConanBuildInfo(build_dir_full_path)
        if conanbuildinfo_file is None:
            raise FileNotFoundError("Unable to locate conanbuildinfo.json")

        self.announce(f"Reading from {conanbuildinfo_file}", 5)
        with open(conanbuildinfo_file) as f:
            conan_build_info = json.loads(f.read())

        for extension in build_ext_cmd.extensions:
            if "tesseract" in extension.libraries:
                extension.libraries.remove("tesseract")

            for dep in conan_build_info['dependencies']:
                extension.include_dirs += dep['include_paths']
                extension.library_dirs += dep['lib_paths']
                extension.libraries += dep['libs']
                extension.define_macros += [(d,) for d in dep['defines']]


setuptools.setup(
    packages=['uiucprescon.ocr'],
    setup_requires=[
        'pytest-runner'
    ],
    install_requires=[],
    test_suite='tests',
    tests_require=[
        'pytest',
    ],
    namespace_packages=["uiucprescon"],
    ext_modules=[
        tesseract_extension
    ],
    cmdclass={
        "build_ext": BuildTesseractExt,
        "build_conan": BuildConan
        # "build_ext": BuildTesseract,
    },
)
