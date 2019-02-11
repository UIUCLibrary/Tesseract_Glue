import setuptools
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

# import itertools
import shutil
import os
import sys
from distutils.version import StrictVersion
from distutils.file_util import copy_file

import urllib.request
import platform
# import subprocess
from typing import List, Tuple, Union
import tarfile
import zipfile

if StrictVersion(setuptools.__version__) < StrictVersion('30.3'):
    print('your setuptools version does not support using setup.cfg. '
          'Upgrade setuptools and repeat the installation.',
          file=sys.stderr
          )

    sys.exit(1)


class CMakeException(RuntimeError):
    pass


class BuildExt(build_ext):
    user_options = build_ext.user_options + [
        ('cmake-exec=', None, "Location of the CMake executable. "
                              "Defaults of CMake located on path")
    ]

    def __init__(self, dist):
        super().__init__(dist)
        self.cmake_source_dir = None
        self.cmake_binary_dir = None
        self._env_vars = None

    def initialize_options(self):
        super().initialize_options()
        self.cmake_exec = shutil.which("cmake")

    def finalize_options(self):
        super().finalize_options()

        if self.cmake_exec is None:
            raise Exception(
                "Unable to locate CMake, Use --cmake-exec to set manually")
        if not os.path.exists(self.cmake_exec):
            raise Exception(
                "Invalid location set to CMake")

    def get_ext_filename(self, fullname):
        ext = self.ext_map[fullname]
        if isinstance(ext, CMakeDependency):
            return f"{fullname}.dll"
        else:
            return super().get_ext_filename(fullname)

    def run(self):
        # super().run()
        for ext in self.extensions:
            if ext.url:
                self.get_source(ext)
                pass
            if ext.prefix_name is None:
                ext.prefix_name = ext.name
            ext.cmake_binary_dir = os.path.join(self.build_temp, "{}-build".format(ext.name))
            self.cmake_binary_dir = self.build_temp
            os.makedirs(ext.cmake_binary_dir, exist_ok=True)

            self.configure_cmake(ext)
            self.build_cmake(ext)
            self.install_cmake(ext)
            self.copy_extensions_to_lib(ext)

            if self.inplace:
                self.copy_extensions_to_src(ext)

    def configure_cmake(self, ext):

        ext.cmake_install_prefix = self.get_install_prefix(ext)
        fetch_content_base_dir = os.path.join(os.path.abspath(self.build_temp), "thirdparty")

        try:
            build_system = self.get_build_generator_name()
        except KeyError as e:

            message = "No known build system generator for the current " \
                      "implementation of Python's compiler {}".format(e)

            raise CMakeException(message)

        configure_command = [
            self.cmake_exec,
            f"-S{os.path.abspath(ext.cmake_source_dir)}",
            f"-B{os.path.abspath(ext.cmake_binary_dir)}",
            f"-DCMAKE_INSTALL_PREFIX={os.path.abspath(ext.cmake_install_prefix)}",
            f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY={os.path.abspath(self.build_temp)}",
            f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG={os.path.abspath(self.build_temp)}",
            f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE={os.path.abspath(self.build_temp)}",
            "-G", build_system,
        ]
        for k, v in ext.cmake_args:
            # To delay any evaluation
            if callable(v):
                v = v()
            configure_command.append(f"{k}={v}")
        configure_command += [
            "-DCMAKE_BUILD_TYPE=Release",
            "-DFETCHCONTENT_BASE_DIR={}".format(fetch_content_base_dir),
        ]

        self.spawn(configure_command)

    def get_install_prefix(self, ext):
        if ext.cmake_install_prefix is not None:
            return os.path.abspath(ext.cmake_install_prefix)

        if isinstance(ext, CMakeDependency):
            install_prefix = os.path.normpath(self.build_temp)
            if ext.prefix_name:
                install_prefix = os.path.join(install_prefix, ext.prefix_name)
            return os.path.abspath(install_prefix)

        return os.path.abspath(self.build_lib)

    def copy_extensions_to_lib(self, ext):
        if isinstance(ext, CMakeDependency):
            if ext.shared_library:
                build_py = self.get_finalized_command('build_py')
                build_cmd = self.get_finalized_command('build_ext')
                fullname = build_cmd.get_ext_fullname(ext.name)
                filename = build_cmd.get_ext_filename(fullname)
                src_filename = os.path.join(self.build_temp, filename)
                package_dir = build_py.get_package_dir("uiucprescon.ocr")
                full_package_dir = os.path.join(self.build_lib, package_dir)
                self.mkpath(full_package_dir)
                # if os.path.exists(src_filename):
                dest_filename = os.path.join(full_package_dir, filename)

                copy_file(
                    src_filename, dest_filename, verbose=self.verbose,
                    dry_run=self.dry_run
                )

    def copy_extensions_to_src(self, ext):
        if ext.shared_library:
            build_py = self.get_finalized_command('build_py')
            build_cmd = self.get_finalized_command('build_ext')
            fullname = build_cmd.get_ext_fullname(ext.name)
            filename = build_cmd.get_ext_filename(fullname)
            # src_filename = os.path.join(self.build_temp, filename)
            package_dir = build_py.get_package_dir("uiucprescon.ocr")
            full_package_dir =os.path.join(self.build_lib, package_dir)
            src_filename = os.path.join(full_package_dir, filename)

            dest_filename = os.path.join(package_dir, filename)
            copy_file(
                src_filename, dest_filename, verbose=self.verbose,
                dry_run=self.dry_run
            )

    @staticmethod
    def get_build_generator_name():
        python_compiler = platform.python_compiler()

        if "GCC" in python_compiler:
            python_compiler = "GCC"

        if "Clang" in python_compiler:
            python_compiler = "Clang"

        cmake_build_systems_lut = {
            'MSC v.1900 64 bit (AMD64)': "Visual Studio 14 2015 Win64",
            'MSC v.1900 32 bit (Intel)': "Visual Studio 14 2015",
            'MSC v.1915 64 bit (AMD64)': "Visual Studio 14 2015 Win64",
            'MSC v.1915 32 bit (Intel)': "Visual Studio 14 2015",
            'GCC': "Unix Makefiles",
            'Clang': "Unix Makefiles",
        }
        # return "Ninja"
        return cmake_build_systems_lut[python_compiler]

    def build_cmake(self, ext):

        build_command = [
            self.cmake_exec,
            "--build", ext.cmake_binary_dir,
            # "--parallel", "{}".format(self.parallel),
            "--config", "release",
        ]
        if self.parallel:
            build_command.extend(["--parallel", str(self.parallel)])

        if "Visual Studio" in self.get_build_generator_name():
            build_command += ["--", "/NOLOGO", "/verbosity:minimal"]

        self.spawn(build_command)

    def install_cmake(self, ext):

        install_command = [
            self.cmake_exec,
            "--build", ext.cmake_binary_dir,
            "--config", "release",
            "--target", "install"
        ]

        self.spawn(install_command)

    def get_modified_env_vars(self, ext):

        if self._env_vars:
            return self._env_vars

        extra_path = set()
        modded_env = os.environ.copy()
        for _, tool in ext.tools.items():
            for __, executable in tool.executable.items():
                extra_path.add(os.path.dirname(executable))
            # for tool in tool:
            #     print(tool.executable)
        new_path = ";".join(extra_path)
        #
        modded_env["PATH"] = "{};{}".format(new_path, modded_env["PATH"])
        self._env_vars = modded_env
        return modded_env

    @staticmethod
    def _get_file_extension(url) -> str:
        if url.endswith(".tar.gz"):
            return ".tar.gz"
        if url.endswith(".zip"):
            return ".zip"
        return os.path.splitext(url)[0]

    @staticmethod
    def locate_cmake_source_root(root):
        for root, dirs, files in os.walk(root):
            for file_name in files:
                if file_name == "CMakeLists.txt":
                    return os.path.abspath(os.path.join(root))
        raise FileNotFoundError("CMakeLists.txt not found")

    def get_source(self, ext):
        source_archive_file_extension = self._get_file_extension(ext.url)
        if ext.url.endswith(source_archive_file_extension):
            src_archive_dst = os.path.join(
                self.build_temp, "".join([ext.name, source_archive_file_extension])
            )

        else:
            src_archive_dst = os.path.join(
                self.build_temp, ext.name, os.path.splitext(ext.url)[1]
            )

        if not os.path.exists(src_archive_dst):
            self._download_source(ext, src_archive_dst)

        source_dest = os.path.join(self.build_temp, "{}-source".format(ext.name))
        self._extract_source(src_archive_dst, source_dest)
        if ext.starting_path is not None:
            source_dest = os.path.join(source_dest, ext.starting_path)
        ext.cmake_source_dir = source_dest
        return source_dest

    @staticmethod
    def _extract_source(source_archive, dst):

        print("Extracting files from {}".format(source_archive))
        if source_archive.endswith(".tar.gz"):
            with tarfile.open(source_archive, "r:gz") as archive:
                for compressed_file in archive:
                    if not os.path.exists(os.path.join(dst, compressed_file.name)):
                        print(" {}".format(compressed_file.name))
                        archive.extract(compressed_file, dst)
        elif source_archive.endswith(".zip"):
            with zipfile.ZipFile(source_archive) as archive:
                for compressed_file in archive.namelist():
                    print(" {}".format(compressed_file))
                    archive.extract(compressed_file, dst)
        else:
            raise Exception("Unknown format to extract {}".format(source_archive))
        print("Extracting files from {}: Done".format(source_archive))

    @staticmethod
    def _download_source(extension, save_as):
        print("Fetching source code for {}".format(extension.name))
        BuildExt.download_file(extension.url, save_as)

    @staticmethod
    def download_file(url, save_as):
        dir_name = os.path.dirname(save_as)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with urllib.request.urlopen(url) as response, open(save_as, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            assert response.getcode() == 200


class CMakeExtension(Extension):
    def __init__(self, name, *args, **kwargs):
        # don't invoke the original build_ext for this special extension
        super().__init__(name, sources=[])
        self.cmake_source_dir = None
        self.cmake_binary_dir = None
        self.cmake_args: List[Tuple[str, Union[str, callable()]]] = kwargs.get("cmake_args", [])
        self.cmake_install_prefix = None
        self.url = None
        self.prefix_name = None
        self.shared_library = True


class CMakeDependency(CMakeExtension):

    def __init__(self, name, url, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.url = url
        self.starting_path = kwargs.get("starting_path")
        self.prefix_name = None



include_path = os.path.join(sys.base_prefix, "include")
lib_path = os.path.join(sys.base_prefix, "Scripts", "python3.dll")

zlib = CMakeDependency(
    name="zlib",
    url="https://www.zlib.net/zlib-1.2.11.tar.gz",
    starting_path="zlib-1.2.11"
)
# Lambdas are use to delay the evaluation until a dependency finished building

libpng = CMakeDependency(
    name="libpng16",
    url="https://download.sourceforge.net/libpng/libpng-1.6.36.tar.gz",
    starting_path="libpng-1.6.36",
    cmake_args=[
        ("-DZLIB_INCLUDE_DIR:PATH", lambda: os.path.join(zlib.cmake_install_prefix, "include")),
        ("-DZLIB_LIBRARY_RELEASE:FILEPATH", lambda: os.path.join(zlib.cmake_install_prefix, "lib", "zlib.lib")),
        ("-DZLIB_LIBRARY_DEBUG:FILEPATH", lambda: os.path.join(zlib.cmake_install_prefix, "lib", "zlibd.lib")),
    ]
)


tiff = CMakeDependency(
    name="tiff",
    url="https://download.osgeo.org/libtiff/tiff-4.0.10.tar.gz",
    cmake_args=[
        ("-DZLIB_INCLUDE_DIR:PATH", lambda: os.path.join(zlib.cmake_install_prefix, "include")),
        ("-DZLIB_LIBRARY_RELEASE:FILEPATH", lambda: os.path.join(zlib.cmake_install_prefix, "lib", "zlib.lib")),
        ("-DZLIB_LIBRARY_DEBUG:FILEPATH", lambda: os.path.join(zlib.cmake_install_prefix, "lib", "zlibd.lib")),
        # ("-DZLIB_ROOT", lambda: zlib.cmake_install_prefix),
        ("-DBUILD_SHARED_LIBS:BOOL", "no"),
       ],
    starting_path="tiff-4.0.10",
   )

tiff.shared_library = False

# TODO: Add a CMakeDependency for openjp2


leptonica = CMakeDependency(
    name="leptonica-1.77.0",
    url="https://github.com/DanBloomberg/leptonica/archive/1.77.0.tar.gz",
    starting_path="leptonica-1.77.0",
    cmake_args=[
        # ("-DZLIB_ROOT", lambda: zlib.cmake_install_prefix),
        ("-DZLIB_INCLUDE_DIR:PATH:", lambda: os.path.join(zlib.cmake_install_prefix, "include")),
        ("-DZLIB_LIBRARY_DEBUG:FILEPATH", lambda: os.path.join(zlib.cmake_install_prefix, "lib", "zlibd.lib")),
        ("-DZLIB_LIBRARY_RELEASE:FILEPATH", lambda: os.path.join(zlib.cmake_install_prefix, "lib", "zlib.lib")),
        ("-DTIFF_INCLUDE_DIR:PATH", lambda: os.path.join(tiff.cmake_install_prefix, "include")),
        ("-DTIFF_LIBRARY:FILEPATH", lambda: os.path.join(tiff.cmake_install_prefix, "lib", "tiff.lib")),
        ("-DPNG_PNG_INCLUDE_DIR:PATH",lambda: os.path.join(libpng.cmake_install_prefix, "include")),
        ("-DPNG_LIBRARY_RELEASE:FILEPATH",lambda: os.path.join(libpng.cmake_install_prefix, "lib", "libpng16.lib")),
    ])

tesseract = CMakeDependency(
    name="tesseract40",
    url="https://github.com/tesseract-ocr/tesseract/archive/4.0.0.tar.gz",
    starting_path="tesseract-4.0.0",
    cmake_args=[
        ("-DBUILD_TRAINING_TOOLS:BOOL", "OFF"),
        ("-DLeptonica_DIR:PATH", lambda: os.path.join(leptonica.cmake_install_prefix, "cmake")),
    ]
)

tesseract_extension = CMakeExtension(
    name="tesseractwrap",
    cmake_args=[
        ("-DPYTHON_EXECUTABLE:FILEPATH", sys.executable),
        ("-DTesseract_ROOT:FILEPATH", lambda: os.path.join(tesseract.cmake_install_prefix)),
        ("-DLeptonica_ROOT:PATH", lambda: os.path.join(leptonica.cmake_install_prefix))
    ]
)
tesseract_extension.cmake_source_dir = os.path.abspath(os.path.dirname(__file__))

setup(
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
        zlib,
        libpng,
        tiff,
        leptonica,
        tesseract,
        tesseract_extension
    ],
    cmdclass={
        "build_ext": BuildExt,
    },
)
