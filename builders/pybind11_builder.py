import abc
from typing import Optional
import pybind11
from setuptools.command.build_ext import build_ext
import os


class BuildPybind11Extension(build_ext):
    user_options = build_ext.user_options + [
        ('cxx-standard=', None, "C++ version to use. Default:11")
    ]

    def initialize_options(self):
        super().initialize_options()
        self.cxx_standard = None

    def finalize_options(self):

        self.cxx_standard = self.cxx_standard or "14"
        super().finalize_options()

    def find_deps(self, lib, search_paths=None):
        search_paths = search_paths or os.environ['path'].split(";")

        search_paths.append(
            self.get_finalized_command("build_clib").build_temp
        )

        for path in search_paths:
            if not os.path.exists(path):
                self.announce(f"Skipping invalid path: {path}", 5)
                continue
            for f in os.scandir(path):
                if f.name.lower() == lib.lower():
                    return f.path

    def find_missing_libraries(self, ext):
        strategies = [
            UseSetuptoolsCompilerFileLibrary(
                compiler=self.compiler,
                dirs=self.library_dirs + ext.library_dirs
            ),
            UseConanFileBuildInfo(
                path=self.get_finalized_command("build_clib").build_temp
            )
        ]
        missing_libs = set(ext.libraries)
        for lib in ext.libraries:
            for strategy in strategies:
                if strategy.locate(lib) is not None:
                    missing_libs.remove(lib)
                    break
        return list(missing_libs)

    def build_extension(self, ext):
        if self.compiler.compiler_type == "unix":
            ext.extra_compile_args.append(f"-std=c++{self.cxx_standard}")
        else:
            ext.extra_compile_args.append(f"/std:c++{self.cxx_standard}")

        super().build_extension(ext)

    def get_pybind11_include_path(self) -> str:
        return pybind11.get_include()


class AbsFindLibrary(abc.ABC):
    @abc.abstractmethod
    def locate(self, library_name) -> Optional[str]:
        """Abstract method for locating a library."""


class UseSetuptoolsCompilerFileLibrary(AbsFindLibrary):
    def __init__(self, compiler, dirs):
        self.compiler = compiler
        self.dirs = dirs

    def locate(self, library_name) -> Optional[str]:
        return self.compiler.find_library_file(self.dirs, library_name)


class UseConanFileBuildInfo(AbsFindLibrary):

    def __init__(self, path) -> None:
        super().__init__()
        self.path = path

    def locate(self, library_name) -> Optional[str]:
        conan_build_info = os.path.join(self.path, "conanbuildinfo.txt")
        if not os.path.exists(conan_build_info):
            return None
        libs = self._parse_file(conan_build_info)
        return library_name in libs

    @staticmethod
    def _parse_file(conan_build_info):
        libs = set()
        with open(conan_build_info, encoding="utf-8") as f:
            found = False
            while True:
                line = f.readline()
                if not line:
                    break
                if line.strip() == "[libs]":
                    found = True
                    continue
                if found:
                    if line.strip() == "":
                        found = False
                        continue
                    if found:
                        libs.add(line.strip())
        return libs
