import itertools
import shutil
import sysconfig
import urllib.request
import os
import sys
from distutils.version import StrictVersion
from functools import lru_cache

from setuptools import setup, Extension
import setuptools

from setuptools.command.build_py import build_py
import subprocess
import typing
from setuptools.command.build_ext import build_ext
import tarfile
import zipfile


TESSERACT_SOURCE_URL = \
    "https://github.com/tesseract-ocr/tesseract/archive/4.0.0-beta.3.tar.gz"

CPPAN_URL = "https://cppan.org/client/cppan-master-Windows-client.zip"

if StrictVersion(setuptools.__version__) < StrictVersion('30.3'):
    print('your setuptools version does not support using setup.cfg. '
          'Upgrade setuptools and repeat the installation.',
          file=sys.stderr
          )

    sys.exit(1)


class Tool(typing.NamedTuple):
    name: str
    url: str
    executable: typing.Dict[str, str]


class BuildExt(build_ext):
    def __init__(self, dist):
        super().__init__(dist)
        self.cmake_source_dir = None
        self.cmake_binary_dir = None
        self._env_vars = None
        self._cmake_path = self._get_cmake_path()

    def _get_cmake_path(self):
        cmake = shutil.which("cmake")
        if cmake:
            return cmake
        raise FileNotFoundError("CMake not found on path")


    def run(self):
        for ext in self.extensions:
            self.cmake_binary_dir = os.path.abspath(os.path.join(self.build_temp, "{}-binary".format(ext.name)))
            os.makedirs(self.cmake_binary_dir, exist_ok=True)
            self.get_required_tools(ext)
            tools = [t.executable for t in ext.tools.values()]

            executables = set()
            for i in [e.keys() for e in tools]:
                for y in i:
                    executables.add(y)
            print("Tools available: {}".format(", ".join(executables)))
            # download_root = self.get_source(ext)
            # source_root = self.locate_cmake_source_root(download_root)
            # self.cmake_source_dir = source_root
            self.install_depends(ext)
            self.configure_cmake(ext)
            self.build_cmake(ext)
            self.install_cmake(ext)
        # super().run()

    def configure_cmake(self, ext):
        os.makedirs(self.cmake_binary_dir, exist_ok=True)
        modded_env = self.get_modified_env_vars(ext)
        #
        source_root = \
            (os.path.relpath(
                os.path.abspath(os.path.dirname(__file__)),
                start=self.cmake_binary_dir))

        # source_root = (os.path.abspath(os.path.dirname(__file__)))
        python_root = sysconfig.get_paths()['data']
        install_prefix = os.path.abspath(self.build_lib)
        configure_command = [
            self._cmake_path, source_root,
            "-GVisual Studio 14 2015 Win64",  # TODO: configure dynamically
            "-DCMAKE_INSTALL_PREFIX={}".format(install_prefix),
            "-DPython3_ROOT_DIR={}".format(python_root),
            # "-DPYTHON_EXTENSION_OUTPUT={}".format(os.path.splitext(self.get_ext_filename(ext.name))[0]),
            "-DBUILD_TESTING:BOOL=NO"
        ]
        configure_stage = subprocess.Popen(
            configure_command,
            env=modded_env,
            cwd=self.cmake_binary_dir
        )

        configure_stage.communicate()

    def build_cmake(self, ext):

        build_command = [
            self._cmake_path,
            "--build", ".",
            # "--parallel", "{}".format(self.parallel),
            "--config", "Release",
        ]

        build_stage = subprocess.Popen(
            build_command,
            env=self.get_modified_env_vars(ext),
            cwd=self.cmake_binary_dir)

        build_stage.communicate()

    def install_cmake(self, ext):

        install_command = [
            self._cmake_path,
            "--build", ".",
            "--config", "Release",
            "--target", "install"
        ]

        install_stage = subprocess.Popen(
            install_command,
            env=self.get_modified_env_vars(ext),
            cwd=self.cmake_binary_dir)

        install_stage.communicate()

        def filter_share_libs(item: os.DirEntry):
            basename, extension = os.path.splitext(item.name)

            if not extension.endswith(".dll") and \
                    not extension.endswith(".pyd"):
                return False

            return True

        """ CPPAN installs all the shared libraries depens that it uses to the 
        bin directory of the tree and all the interface libraries to the lib 
        directory. 
        I cannot find a way to change this behavior, so all dll files should be 
        moved to the python module and the .lib files need to be deleted before
        python can create a wheel. 
        """
        if self.inplace == 1:
            dest_root = os.path.abspath(os.path.dirname(__file__))
        else:
            dest_root = self.build_lib

        install_file_paths = [
            os.path.join(self.build_lib, "bin"),
            os.path.join(self.build_lib, "ocr"),

        ]
        for m in itertools.chain(map(os.scandir, install_file_paths)):
            for dll in filter(filter_share_libs, m):
                dll_dest = os.path.join(dest_root, "ocr", dll.name)
                shutil.move(dll.path, os.path.join(dll_dest))

        generated_bin_directory = os.path.join(self.build_lib, "bin")
        generated_lib_directory = os.path.join(self.build_lib, "lib")
        generated_dirs = [generated_bin_directory, generated_lib_directory]

        for generated_dir in generated_dirs:
            if os.path.exists(generated_dir):
                print("Removing {}".format(generated_dir))
                shutil.rmtree(generated_dir)


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
    def _get_file_extension(url)->str:
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
        return source_dest

    def get_required_tools(self, ext):
        for tool_name, tool in ext.tools.items():
            file_extension = self._get_file_extension(tool.url)
            download_dst = os.path.join(self.build_temp, "{}{}".format(tool_name, file_extension))
            if not os.path.exists(download_dst):
                print("Downloading {}".format(tool_name))
                self.download_file(tool.url, download_dst)

            dst = os.path.join(self._get_tools_dir(), tool_name)
            if not os.path.exists(dst):
                self._extract_source(download_dst, dst)

            tool_executables = {}
            for executable in self._find_executables(dst):
                executable_name = \
                    os.path.splitext(os.path.basename(executable))[0]
                tool_executables[executable_name] = os.path.abspath(executable)

            ext.tools[tool_name] = Tool(tool_name, tool.url, tool_executables)

    def _find_executables(self, root)->typing.Iterable[str]:
        for root, dirs, files in os.walk(root):
            for filename in files:
                full_path = os.path.join(root, filename)
                if os.access(full_path, os.X_OK):
                    yield full_path

    def install_depends(self, ext):
        for command in ext.configuration_commands:
            command(self, ext)


    def _get_tools_dir(self):
        """ Returns directory to store any helper tools"""

        tools_dir = os.path.join(self.build_temp, "tools")
        if not os.path.exists(tools_dir):
            os.makedirs(tools_dir)
        return tools_dir

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
    def __init__(self, name):
        # don't invoke the original build_ext for this special extension
        super().__init__(name, sources=[])


class DownloadCMakeExtension(CMakeExtension):

    def __init__(self, name, url):
        super().__init__(name)
        self.url = url
        self.cmake_source_dir = None
        self.cmake_binary_dir = None
        self.tools: typing.Dict[str, Tool] = dict()
        self.configuration_commands = []

    def add_required_tool(self, name, url):
        self.tools[name] = Tool(name, url, dict())

    def add_configure_command(self, callback):
        self.configuration_commands.append(callback)

def install_cppan(build, ext):
    cppan = ext.tools['CPPAN']
    executable = cppan.executable['cppan']
    subprocess.run([executable, ], cwd=build.build_temp)

tesseract_extension = DownloadCMakeExtension("tesseractwrap", TESSERACT_SOURCE_URL)

tesseract_extension.add_required_tool("CPPAN", CPPAN_URL)
tesseract_extension.add_configure_command(install_cppan)

setup(
    packages=['ocr'],
    setup_requires=[
        'pytest-runner'
    ],
    install_requires=[],
    test_suite='tests',
    tests_require=[
        'pytest',
    ],
    ext_modules=[tesseract_extension],
    cmdclass={
        # 'build_py': BuildPyCommand,
        "build_ext": BuildExt,
    },
)
