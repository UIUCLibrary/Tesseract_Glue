from subprocess import Popen
from ctypes.util import find_library
import setuptools
from setuptools.command.build_ext import build_ext
import shutil
import os
import sys
from distutils.version import StrictVersion
# from distutils.file_util import copy_file
# import distutils.ccompiler
import urllib.request
import platform
from typing import List, Tuple, Union
import tarfile
import zipfile

PACKAGE_NAME = "uiucprescon.ocr"

# nasm = shutil.which("nasm")

if StrictVersion(setuptools.__version__) < StrictVersion('30.3'):
    print('your setuptools version does not support using setup.cfg. '
          'Upgrade setuptools and repeat the installation.',
          file=sys.stderr
          )

    sys.exit(1)


class CMakeException(RuntimeError):
    pass


class CMakeToolchainWriter:

    def __init__(self) -> None:
        super().__init__()
        self._cache_values = dict()

    def _generate_text(self) -> str:
        lines = []
        for k, v in self._cache_values.items():
            lines.append(f"set({k} \"{v}\")")
        return "\n".join(lines)

    def write(self, filename) -> None:
        with open(filename, "w") as wf:
            wf.write(self._generate_text())
            wf.write("\n")

    def add_path(self, key: str, value: str):
        self._cache_values[key] = value.replace("\\", "/")

    def add_string(self, key: str, value: str):
        self._cache_values[key] = value


class BuildExt(build_ext):
    user_options = build_ext.user_options + [
        ('cmake-exec=', None, "Location of the CMake executable. "
                              "Defaults of CMake located on path"),
        ('cmake-generator=', None, "Build system CMake generates."),
        ('nasm-exec=', None, "Location of the NASM executable. "
                             "Defaults of NASM located on path")
    ]

    def __init__(self, dist):
        super().__init__(dist)
        self.cmake_source_dir = None
        self.cmake_binary_dir = None
        self._env_vars = None
        self.library_install_dir = ""
        self.build_configuration = "release"

    @property
    def package_dir(self):
        build_py = self.get_finalized_command('build_py')
        return build_py.get_package_dir(PACKAGE_NAME)

    def initialize_options(self):
        super().initialize_options()
        self.cmake_exec = shutil.which("cmake")
        self.nasm_exec = shutil.which("nasm")
        if shutil.which("ninja") is not None:
            self.cmake_generator = "Ninja"
        else:
            self.cmake_generator = None


    def finalize_options(self):
        super().finalize_options()

        if self.cmake_exec is None:
            raise Exception(
                "Unable to locate CMake, Use --cmake-exec to set manually")
        if not os.path.exists(self.cmake_exec):
            raise Exception(
                "Invalid location set to CMake")
        pass

    def get_ext_filename(self, fullname):
        ext = self.ext_map[fullname]
        if isinstance(ext, CMakeDependency):
            return os.path.join("bin", f"{fullname}.dll")
        else:
            return super().get_ext_filename(fullname)

    def build_extensions(self):
        self.toolchain_file = os.path.abspath(os.path.join(self.build_temp, "toolchain.cmake"))

        if os.path.exists(self.toolchain_file):
            self.announce("Using CMake Toolchain file {}.".format(self.toolchain_file), 2)
        else:
            self.write_toolchain_file(self.toolchain_file)

        for ext in self.extensions:
            with self._filter_build_errors(ext):
                self.build_extension(ext)

    def run(self):
        for ext in self.extensions:
            ext.cmake_install_prefix = self.get_install_prefix(ext)
            ext.cmake_binary_dir = os.path.join(self.build_temp, "{}-build".format(ext.name))
        super().run()

    def build_extension(self, ext):
        _compiler = self.compiler

        try:
            if isinstance(ext, CMakeDependency) or isinstance(ext, CMakeExtension):
                if ext.url:
                    self.get_source(ext)
                self.compiler = self.shlib_compiler

                if not self.compiler.initialized:
                    self.compiler.initialize()
                self.mkpath(ext.cmake_binary_dir)

                self.configure_cmake(ext)

                self.build_cmake(ext)

                if self.needs_to_install(ext):
                    self.install_cmake(ext)

            # Tesseract 4.0 uses OpenMP on Windows
            openMP_library = find_library("VCOMP140")
            if openMP_library is not None:
                self.announce("Including OpenMP runtime")
                self.copy_file(openMP_library, os.path.join(self.build_lib, self.package_dir, "tesseract", "bin"))

            if ext._needs_stub:
                cmd = self.get_finalized_command('build_py').build_lib
                self.write_stub(cmd, ext)

        finally:
            self.compiler = _compiler


    def needs_to_run_configure(self, ext) -> bool:

        if self.force:
            return True

        cmake_cache = os.path.join(ext.cmake_binary_dir, "CMakeCache.txt")
        if not os.path.exists(cmake_cache):
            self.announce("CMake has not generated needed CMakeCache.txt", 1)
            return True

        return False

    def needs_to_install(self, ext) -> bool:
        if self.force:
            return True

        install_manifest = os.path.join(ext.cmake_binary_dir,
                                        "install_manifest.txt")

        if not os.path.exists(install_manifest):
            return True

        with open(install_manifest, "r") as f:
            for line in f:
                install_file = line.strip()
                if not os.path.exists(install_file):
                    return True
        return False

    def configure_cmake(self, ext):

        configure_command = [
            self.cmake_exec,
            f"{os.path.abspath(ext.cmake_source_dir)}",
            f"-B{os.path.abspath(ext.cmake_binary_dir)}",
            f"-DCMAKE_INSTALL_PREFIX={os.path.abspath(ext.cmake_install_prefix)}",
            f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY={os.path.abspath(self.build_temp)}",
        ]

        if self.debug is not None:
            configure_command.append(f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG={os.path.abspath(self.build_temp)}")
        else:
            configure_command.append(f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE={os.path.abspath(self.build_temp)}")

        try:

            if self.cmake_generator is not None:
                configure_command += ["-G", self.cmake_generator]
            else:

                if 'MSC v.19' in platform.python_compiler():
                    configure_command += ["-T", "v140"]

            configure_command.insert(2, f"-DCMAKE_TOOLCHAIN_FILE:FILEPATH=\"{self.toolchain_file}\"")

        except KeyError as e:

            message = "No known build system generator for the current " \
                      "implementation of Python's compiler {}".format(e)

            raise CMakeException(message)

        for k, v in ext.cmake_args:
            # To delay any evaluation
            if callable(v):
                v = v()
            configure_command.append(f"{k}={v}")
        configure_command += [
            "-DCMAKE_BUILD_TYPE={}".format(self.build_configuration),
        ]
        self.compiler_spawn(configure_command)

    def write_toolchain_file(self, toolchain_file):

        self.announce("Generating CMake Toolchain file", 2)
        if not self.compiler.initialized:
            self.compiler.initialize()

        self.mkpath(self.build_temp)
        writer = CMakeToolchainWriter()
        writer.add_string(key="CMAKE_SYSTEM_NAME", value=platform.system())

        writer.add_string(key="CMAKE_SYSTEM_PROCESSOR", value=platform.machine())

        writer.add_path(key="CMAKE_C_COMPILER", value=self.compiler.cc)
        writer.add_path(key="CMAKE_CXX_COMPILER", value=self.compiler.cc)
        writer.add_path(key="CMAKE_LINKER", value=self.compiler.linker)
        writer.add_path(key="CMAKE_RC_COMPILER", value=self.compiler.rc)
        writer.add_path(key="FETCHCONTENT_BASE_DIR", value=os.path.abspath(os.path.join(self.build_temp,"thirdparty")))
        if self.nasm_exec:
            writer.add_path(key="CMAKE_ASM_NASM_COMPILER", value=os.path.normcase(self.nasm_exec))

        writer.write(toolchain_file)
        self.announce("Generated CMake Toolchain file: {}".format(toolchain_file))

    def get_install_prefix(self, ext):
        if ext.cmake_install_prefix is not None:
            return os.path.abspath(ext.cmake_install_prefix)
        #
        if isinstance(ext, CMakeDependency) or isinstance(ext, CMakeExtension):

            if isinstance(ext, CMakeDependency):
                install_prefix = os.path.join(self.build_lib, self.package_dir, self.library_install_dir)
            else:
                install_prefix = self.build_lib

            if ext.prefix_name is not None:
                install_prefix = os.path.join(install_prefix, ext.prefix_name)

            return os.path.abspath(install_prefix)

        return os.path.abspath(self.build_lib)

    def get_ext_fullpath(self, ext_name):
        return super().get_ext_fullpath(ext_name)

    def copy_extensions_to_source(self):
        build_py = self.get_finalized_command('build_py')
        for ext in self.extensions:
            fullname = self.get_ext_fullname(ext.name)
            filename = self.get_ext_filename(fullname)
            if ext.shared_library and (isinstance(ext, CMakeDependency) or isinstance(ext, CMakeExtension)):
                src_filename = os.path.join(self.build_lib, self.package_dir)
                if isinstance(ext, CMakeDependency):
                    src_filename = os.path.join(src_filename, "tesseract")
                    full_package_dir = \
                        os.path.join(self.package_dir,
                                     self.library_install_dir)
                else:
                    full_package_dir = self.package_dir
                    src_filename = os.path.join(self.build_lib,
                                                self.package_dir)
                src_filename = os.path.join(src_filename, filename)
                dest_filename = os.path.join(full_package_dir, filename)
                self.mkpath(os.path.dirname(dest_filename))
                self.copy_file(src_filename, dest_filename)

                if ext._needs_stub:
                    self.write_stub(dest_filename or os.curdir, ext, True)

            # if ext._needs_stub:
            #     self.write_stub(full_package_dir or os.curdir, ext, True)

    def copy_extensions_to_lib(self, ext):
        if isinstance(ext, CMakeDependency):
            if ext.shared_library:
                build_cmd = self.get_finalized_command('build_ext')
                fullname = build_cmd.get_ext_fullname(ext.name)
                filename = build_cmd.get_ext_filename(fullname)
                src_filename = os.path.join(self.build_temp, filename)
                full_package_dir = os.path.join(self.build_lib,
                                                self.package_dir,
                                                self.library_install_dir,
                                                "bin")

                self.mkpath(full_package_dir)
                dest_filename = os.path.join(full_package_dir, filename)

                self.copy_file(src_filename, dest_filename)


    @staticmethod
    def get_build_generator_name():
        python_compiler = platform.python_compiler()

        if "GCC" in python_compiler:
            return "Unix Makefiles"

        if "Clang" in python_compiler:
            return "Unix Makefiles"

        if 'MSC v.19' in python_compiler:
            return "Visual Studio 14 2015"

    def build_cmake(self, ext):

        build_command = [
            self.cmake_exec,
            "--build", os.path.abspath(ext.cmake_binary_dir),
            "--config", self.build_configuration,
        ]
        if self.parallel is not None:
            build_command += ["--parallel", str(self.parallel)]

        self.compiler_spawn(build_command)
        pass

    def compiler_spawn(self, cmd):
        old_env_vars = os.environ.copy()
        old_path = os.getenv("Path")
        try:
            os.environ["LIB"] = ";".join(self.compiler.library_dirs)
            os.environ["INCLUDE"] = ";".join(self.compiler.include_dirs)

            paths = [self.build_temp]
            paths += old_path.split(";")
            paths += self.compiler._paths.split(";")
            new_value_path = ";".join(paths)
            os.environ["Path"] = new_value_path
            self.compiler.spawn(cmd)
        finally:
            os.environ = old_env_vars
            os.environ["Path"] = old_path

    def install_cmake(self, ext):

        install_command = [
            self.cmake_exec,
            "--build", os.path.abspath(ext.cmake_binary_dir),
            "--config", self.build_configuration,
            "--target", "install"
        ]
        self.compiler_spawn(install_command)
        # p = Popen(install_command)
        # p.communicate()
        pass

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
                self.build_temp, "".join([ext.name,
                                          source_archive_file_extension])
            )

        else:
            src_archive_dst = os.path.join(
                self.build_temp, ext.name, os.path.splitext(ext.url)[1]
            )

        if not os.path.exists(src_archive_dst):
            self._download_source(ext, src_archive_dst)

        source_dest = os.path.join(self.build_temp,
                                   "{}-source".format(ext.name))

        self._extract_source(src_archive_dst, source_dest)
        if ext.starting_path is not None:
            source_dest = os.path.join(source_dest, ext.starting_path)
        ext.cmake_source_dir = source_dest
        return source_dest

    def _extract_source(self, source_archive, dst):

        if source_archive.endswith(".tar.gz"):
            with tarfile.open(source_archive, "r:gz") as archive:
                for compressed_file in archive:
                    if not os.path.exists(
                            os.path.join(dst, compressed_file.name)):
                        self.announce(
                            "Extracting {}".format(compressed_file.name))

                        archive.extract(compressed_file, dst)
        elif source_archive.endswith(".zip"):
            with zipfile.ZipFile(source_archive) as archive:
                for compressed_file in archive.namelist():
                    self.announce("Extracting {}".format(compressed_file))
                    archive.extract(compressed_file, dst)
        else:
            raise Exception(
                "Unknown format to extract {}".format(source_archive))

    def _download_source(self, extension, save_as):
        self.announce("Fetching source code for {}".format(extension.name))
        BuildExt.download_file(extension.url, save_as)

    @staticmethod
    def download_file(url, save_as):
        dir_name = os.path.dirname(save_as)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with urllib.request.urlopen(url) as response:
            with open(save_as, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
                assert response.getcode() == 200


class BuildTesseract(BuildExt):
    user_options = BuildExt.user_options

    def __init__(self, dist):
        super().__init__(dist)
        self.library_install_dir = "tesseract"


class CMakeExtension(setuptools.Extension):
    def __init__(self, name, *args, **kwargs):
        # don't invoke the original build_ext for this special extension
        super().__init__(name, sources=[])
        self.cmake_source_dir = None
        self.cmake_binary_dir = None
        self.cmake_args: List[Tuple[str, Union[str, callable()]]] = \
            kwargs.get("cmake_args", [])

        self.cmake_install_prefix = None
        self.url = None
        self.prefix_name = None
        self.shared_library = True


class CMakeDependency(setuptools.extension.Library):

    def __init__(self, name, url, *args, **kwargs):

        self.starting_path = kwargs.get("starting_path")

        self.cmake_args: List[Tuple[str, Union[str, callable()]]] = \
            kwargs.get("cmake_args", [])

        # delete keys before sending it to super because you'll get warnings
        # otherwise for these kwargs
        if "starting_path" in kwargs:
            del kwargs['starting_path']

        if "cmake_args" in kwargs:
            del kwargs["cmake_args"]

        super().__init__(name, *args, **kwargs, sources=[])
        self.url = url
        self.prefix_name = None
        self.cmake_source_dir = None
        self.cmake_binary_dir = None

        self.cmake_install_prefix = None
        self.shared_library = True
        self.name = name




zlib = CMakeDependency(
    name="zlib",
    url="https://www.zlib.net/zlib-1.2.11.tar.gz",
    starting_path="zlib-1.2.11",
    language="C"
)
# Lambdas are use to delay the evaluation until a dependency finished building

libpng = CMakeDependency(
    name="libpng16",
    url="https://github.com/glennrp/libpng/archive/v1.6.36.tar.gz",
    starting_path="libpng-1.6.36",
    cmake_args=[
        ("-DZLIB_INCLUDE_DIR:PATH",
            lambda: os.path.join(
                zlib.cmake_install_prefix, "include")),
        ("-DPNG_TESTS:BOOL", "FALSE"),
        ("-DZLIB_LIBRARY_RELEASE:FILEPATH",
            lambda: os.path.join(
                zlib.cmake_install_prefix, "lib", "zlib.lib")),
        ("-DZLIB_LIBRARY_DEBUG:FILEPATH",
            lambda: os.path.join(
                zlib.cmake_install_prefix, "lib", "zlibd.lib")),
    ]
)

libjpeg = CMakeDependency(
    name="jpeg62",
    url="https://github.com/libjpeg-turbo/libjpeg-turbo/archive/2.0.1.tar.gz",
    starting_path="libjpeg-turbo-2.0.1",
    cmake_args=[
        ("-DENABLE_STATIC:BOOL", "False"),
        ("-DWITH_TURBOJPEG:BOOL", "OFF"),
    ]

)


tiff = CMakeDependency(
    name="tiff",
    url="https://download.osgeo.org/libtiff/tiff-4.0.10.tar.gz",
    cmake_args=[
        ("-DZLIB_INCLUDE_DIR:PATH",
            lambda: os.path.join(
                zlib.cmake_install_prefix, "include")),
        ("-DZLIB_LIBRARY_RELEASE:FILEPATH",
            lambda: os.path.join(
                zlib.cmake_install_prefix, "lib", "zlib.lib")),
        ("-DZLIB_LIBRARY_DEBUG:FILEPATH",
            lambda: os.path.join(
                zlib.cmake_install_prefix, "lib", "zlibd.lib")),
        ("-DJPEG_INCLUDE_DIR:PATH",
            lambda: os.path.join(
                libjpeg.cmake_install_prefix, "include")),
        ("-DJPEG_LIBRARY:FILEPATH",
            lambda: os.path.join(
                libjpeg.cmake_install_prefix, "lib", "jpeg.lib")),
       ],
    starting_path="tiff-4.0.10",
   )

openjpeg = CMakeDependency(
    name="openjp2",
    url="https://github.com/uclouvain/openjpeg/archive/v2.3.0.tar.gz",
    starting_path="openjpeg-2.3.0",
    cmake_args=[
        ("-DBUILD_CODEC:BOOL", "OFF"),
    ]
)

leptonica = CMakeDependency(
    name="leptonica-1.77.0",
    url="https://github.com/DanBloomberg/leptonica/archive/1.77.0.tar.gz",
    starting_path="leptonica-1.77.0",
    cmake_args=[
        ("-DZLIB_INCLUDE_DIR:PATH:",
            lambda: os.path.join(
                zlib.cmake_install_prefix, "include")),
        ("-DZLIB_LIBRARY_DEBUG:FILEPATH",
            lambda: os.path.join(
                zlib.cmake_install_prefix, "lib", "zlibd.lib")),
        ("-DZLIB_LIBRARY_RELEASE:FILEPATH",
            lambda: os.path.join(
                zlib.cmake_install_prefix, "lib", "zlib.lib")),
        ("-DTIFF_INCLUDE_DIR:PATH",
            lambda: os.path.join(
                tiff.cmake_install_prefix, "include")),
        ("-DTIFF_LIBRARY:FILEPATH",
            lambda: os.path.join(
                tiff.cmake_install_prefix, "lib", "tiff.lib")),
        ("-DJPEG_INCLUDE_DIR:PATH",
            lambda: os.path.join(
                libjpeg.cmake_install_prefix, "include")),
        ("-DJPEG_LIBRARY:FILEPATH",
            lambda: os.path.join(
                libjpeg.cmake_install_prefix, "lib", "jpeg.lib")),
        ("-DPNG_PNG_INCLUDE_DIR:PATH",
            lambda: os.path.join(
                libpng.cmake_install_prefix, "include")),
        ("-DPNG_LIBRARY_RELEASE:FILEPATH",
            lambda: os.path.join(
                libpng.cmake_install_prefix, "lib", "libpng16.lib")),
        ("-DJP2K_FOUND:BOOL", "TRUE"),
        ("-DJP2K_INCLUDE_DIRS:PATH",
            lambda: os.path.join(
                openjpeg.cmake_install_prefix, "include", "openjpeg-2.3")),
        ("-DJP2K_LIBRARIES:FILEPATH",
            lambda: os.path.join(
                openjpeg.cmake_install_prefix, "lib", "openjp2.lib"))
    ])

tesseract = CMakeDependency(
    name="tesseract40",
    url="https://github.com/tesseract-ocr/tesseract/archive/4.0.0.tar.gz",
    starting_path="tesseract-4.0.0",
    cmake_args=[
        ("-DBUILD_TRAINING_TOOLS:BOOL", "OFF"),
        ("-DLeptonica_DIR:PATH",
            lambda: os.path.join(leptonica.cmake_install_prefix, "cmake")),
    ]
)

tesseract_extension = CMakeExtension(
    name="tesseractwrap",
    cmake_args=[
        ("-DPYTHON_EXECUTABLE:FILEPATH", sys.executable),
        ("-DTesseract_ROOT:FILEPATH",
            lambda: os.path.join(tesseract.cmake_install_prefix)),
        ("-DLeptonica_ROOT:PATH",
            lambda: os.path.join(leptonica.cmake_install_prefix))
    ]
)
tesseract_extension.cmake_source_dir = \
    os.path.abspath(os.path.dirname(__file__))

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
        zlib,
        libpng,
        libjpeg,
        tiff,
        openjpeg,
        leptonica,
        tesseract,
        tesseract_extension
    ],
    cmdclass={
        "build_ext": BuildTesseract,
    },
)
