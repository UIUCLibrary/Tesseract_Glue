import logging
import os
import sys
import shutil
import abc
from typing import Iterable, Any, Dict, List, Union

import setuptools

# from conans.model.profile import Profile

class ConanBuildInfoParser:
    def __init__(self, fp):
        self._fp = fp

    def parse(self) -> Dict[str, List[str]]:
        data = dict()
        for subject_chunk in self.iter_subject_chunk():
            subject_title = subject_chunk[0][1:-1]

            data[subject_title] = subject_chunk[1:]
        return data

    def iter_subject_chunk(self) -> Iterable[Any]:
        buffer = []
        for line in self._fp:
            line = line.strip()
            if len(line) == 0:
                continue
            if line.startswith("[") and line.endswith("]") and len(buffer) > 0:
                yield buffer
                buffer.clear()
            buffer.append(line)
        yield buffer
        buffer.clear()


class AbsConanBuildInfo(abc.ABC):
    @abc.abstractmethod
    def parse(self, filename: str) -> Dict[str, str]:
        pass


class ConanBuildInfoTXT(AbsConanBuildInfo):

    def parse(self, filename: str) -> Dict[str, Union[str, List[str]]]:
        with open(filename, "r") as f:
            parser = ConanBuildInfoParser(f)
            data = parser.parse()
            definitions = data['defines']
            include_paths = data['includedirs']
            lib_paths = data['libdirs']
            bin_paths = data['bindirs']
            libs = data['libs']

        return {
            "definitions": definitions,
            "include_paths": list(include_paths),
            "lib_paths": list(lib_paths),
            "bin_paths": list(bin_paths),
            "libs": list(libs),

        }


class CompilerInfoAdder:

    def __init__(self, build_ext_cmd) -> None:
        super().__init__()
        self._build_ext_cmd = build_ext_cmd
        if build_ext_cmd.compiler is None:
            self._place_to_add = build_ext_cmd
        else:
            self._place_to_add = build_ext_cmd.compiler

    def add_libs(self, libs: List[str]):
        extension_deps = set()
        for lib in reversed(libs):
            # if lib == self.output_library_name:
            #     continue
            if lib not in self._place_to_add.libraries and lib not in extension_deps:
                self._place_to_add.libraries.insert(0, lib)

    def add_lib_dirs(self, lib_dirs: List[str]):
        for path in reversed(lib_dirs):
            assert os.path.exists(path)
            if path not in self._place_to_add.library_dirs:
                self._place_to_add.library_dirs.insert(0, path)

    def add_include_dirs(self, include_dirs: List[str]):
        for path in reversed(include_dirs):
            if path not in self._place_to_add.include_dirs:
                self._place_to_add.include_dirs.insert(0, path)
            else:
                self._place_to_add.compiler.include_dirs.insert(0, path)


class BuildConan(setuptools.Command):
    user_options = [
        ('conan-cache=', None, 'conan cache directory')
    ]

    description = "Get the required dependencies from a Conan package manager"

    def initialize_options(self):
        self.conan_cache = None

    def __init__(self, dist, **kw):
        super().__init__(dist, **kw)
        self.output_library_name = "tesseract"

    def finalize_options(self):
        if self.conan_cache is None:
            build_ext_cmd = self.get_finalized_command("build_ext")
            build_dir = build_ext_cmd.build_temp

            self.conan_cache = \
                os.path.join(
                    os.environ.get("CONAN_USER_HOME", build_dir),
                    ".conan"
                )

    def getConanBuildInfo(self, root_dir):
        for root, dirs, files in os.walk(root_dir):
            for f in files:
                if f == "conanbuildinfo.json":
                    return os.path.join(root, f)
        return None

    def _get_deps(self, build_dir=None, conan_cache=None):
        build_dir = build_dir or self.get_finalized_command("build_clib").build_temp
        from conans.client import conan_api
        conan = conan_api.Conan(cache_folder=os.path.abspath(conan_cache))
        # conan_options = ['openjpeg:shared=True']
        conan_options = []
        build = ['missing']

        build_ext_cmd = self.get_finalized_command("build_ext")
        settings = []
        if build_ext_cmd.debug is not None:
            settings.append("build_type=Debug")
        #     FIXME: This should be the setup.py file dir
        conanfile_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        build_dir_full_path = os.path.abspath(build_dir)
        conan.install(
            options=conan_options,
            cwd=build_dir,
            settings=settings,
            build=build if len(build) > 0 else None,
            path=conanfile_path,
            install_folder=build_dir_full_path,
            # profile_build=profile
        )

    def add_deps_to_compiler(self, metadata) -> None:
        build_ext_cmd = self.get_finalized_command("build_ext")
        compiler_adder = CompilerInfoAdder(build_ext_cmd)

        include_dirs = metadata['include_paths']
        compiler_adder.add_include_dirs(include_dirs)
        self.announce(
            f"Added the following paths to include path {', '.join(include_dirs)} ",
            5)

        lib_paths = metadata['lib_paths']
        compiler_adder.add_lib_dirs(lib_paths)
        self.announce(
            f"Added the following paths to library path {', '.join(metadata['lib_paths'])} ",
            5)

        libs = metadata['libs']
        if self.output_library_name in libs:
            libs.remove(self.output_library_name)

        compiler_adder.add_libs(libs)

        if build_ext_cmd.compiler is not None:
            build_ext_cmd.compiler.macros += [(d, ) for d in metadata['definitions']]
        else:
            if hasattr(build_ext_cmd, "macros"):
                build_ext_cmd.macros += [(d, ) for d in metadata['definitions']]
            else:
                build_ext_cmd.macros = [(d, ) for d in metadata['definitions']]

        for extension in build_ext_cmd.extensions:
            # fixme
            if sys.platform == "windows":
                if self.output_library_name in extension.libraries:
                    extension.libraries.remove(self.output_library_name)

            for lib in metadata['libs']:
                if lib == self.output_library_name:
                    continue
                extension.libraries.append(lib)
            extension.define_macros += [(d,) for d in metadata['definitions']]


    def run(self):
        # self.reinitialize_command("build_ext")
        build_clib = self.get_finalized_command("build_clib")

        build_dir = build_clib.build_temp

        build_dir_full_path = os.path.abspath(build_dir)
        conan_cache = self.conan_cache
        self.mkpath(conan_cache)
        self.mkpath(build_dir_full_path)
        self.mkpath(os.path.join(build_dir_full_path, "lib"))
        self.announce(f"Using {conan_cache} for conan cache", 5)

        self._get_deps(conan_cache=conan_cache)
        conaninfotext = os.path.join(build_dir, "conaninfo.txt")
        if os.path.exists(conaninfotext):
            with open(conaninfotext) as r:
                self.announce(r.read(), 5)

        conanbuildinfotext = os.path.join(build_dir, "conanbuildinfo.txt")
        if os.path.exists(conanbuildinfotext):
            with open(conanbuildinfotext) as r:
                self.announce(r.read(), 5)

        assert os.path.exists(conanbuildinfotext)
        metadata_strategy = ConanBuildInfoTXT()
        text_md = metadata_strategy.parse(conanbuildinfotext)
        self.add_deps_to_compiler(metadata=text_md)
