import logging
import os
import shutil
from typing import Iterable, Any, Dict, List

import setuptools


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


class BuildConan(setuptools.Command):
    user_options = [
        ('conan-exec=', "c", 'conan executable'),
        ('conan-cache=', None, 'conan cache directory')
    ]

    description = "Get the required dependencies from a Conan package manager"

    def initialize_options(self):
        self.conan_exec = None
        self.conan_cache = None

    def finalize_options(self):
        if self.conan_exec is None:
            self.conan_exec = shutil.which("conan")
            if self.conan_exec is None:
                raise Exception("missing conan_exec")
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

    def get_from_txt(self, conanbuildinfo_file):
        definitions = []
        include_paths = []
        lib_paths = []
        bin_paths = []
        libs = []

        with open(conanbuildinfo_file, "r") as f:
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

    def run(self):
        # self.reinitialize_command("build_ext")
        build_clib = self.get_finalized_command("build_clib")

        build_dir = build_clib.build_temp

        build_dir_full_path = os.path.abspath(build_dir)
        conan_cache = self.conan_cache
        self.mkpath(conan_cache)
        self.mkpath(build_dir_full_path)
        self.mkpath(os.path.join(build_dir_full_path, "lib"))
        from conans.client import conan_api, conf
        from conans.model.profile import Profile
        logger = logging.Logger(__name__)
        conan_profile_cache = os.path.join(build_dir, "profiles")
        settings = []
        for name, value in conf.detect.detect_defaults_settings(logger, conan_profile_cache):
            settings.append(f"{name}={value}")
        # s = conan_api.cmd_profile_get(profile_name="projectbuild", key="settings.os", cache_profiles_path=conan_profile_cache)
        self.announce(f"Using {conan_cache} for conan cache", 5)
        conan = conan_api.Conan(cache_folder=os.path.abspath(conan_cache))
        conan_options = []
        build = ['missing']

        build_ext_cmd = self.get_finalized_command("build_ext")
        if build_ext_cmd.debug is not None:
            settings.append("build_type=Debug")
        #     FIXME: This should be the setup.py file dir
        conanfile_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        conan.install(
            options=conan_options,
            cwd=build_dir,
            settings=settings,
            build=build if len(build) > 0 else None,
            path=conanfile_path,
            install_folder=build_dir_full_path,
            # profile_build=profile
        )
        conaninfotext = os.path.join(build_dir, "conaninfo.txt")
        if os.path.exists(conaninfotext):
            with open(conaninfotext) as r:
                self.announce(r.read(), 5)

        conanbuildinfotext = os.path.join(build_dir, "conanbuildinfo.txt")
        assert os.path.exists(conanbuildinfotext)
        text_md = self.get_from_txt(conanbuildinfotext)
        for path in text_md['include_paths']:
            if build_ext_cmd.compiler is None:
                if path not in build_ext_cmd.include_dirs:
                    build_ext_cmd.include_dirs.insert(0, path)
            else:
                build_ext_cmd.compiler.include_dirs.insert(0, path)

        for path in text_md['lib_paths']:
            assert os.path.exists(path)
            if build_ext_cmd.compiler is None:
                if path not in build_ext_cmd.library_dirs:
                    build_ext_cmd.library_dirs.insert(0, path)
            else:
                build_ext_cmd.compiler.library_dirs.insert(0, path)

        extension_deps = set()
        for library_deps in [l.libraries for l in
                             build_ext_cmd.ext_map.values()]:
            extension_deps = extension_deps.union(library_deps)

        for lib in text_md['libs']:
            if lib == "tesseract":
                continue
            if lib not in build_ext_cmd.libraries and lib not in extension_deps:
                if build_ext_cmd.compiler is None:
                    build_ext_cmd.libraries.insert(0, lib)
                else:
                    build_ext_cmd.compiler.libraries.insert(0, lib)
        # ===================================
        if build_ext_cmd.compiler is not None:
            build_ext_cmd.compiler.macros += [(d, ) for d in text_md['definitions']]
        else:
            if hasattr(build_ext_cmd, "macros"):
                build_ext_cmd.macros += [(d, ) for d in text_md['definitions']]
            else:
                build_ext_cmd.macros = [(d, ) for d in text_md['definitions']]
        # ===================================
        for extension in build_ext_cmd.extensions:
            if "tesseract" in extension.libraries:
                extension.libraries.remove("tesseract")
            for lib in text_md['libs']:
                if lib == "tesseract`":
                    continue
                extension.libraries.append(lib)
            extension.define_macros += [(d,) for d in text_md['definitions']]
        # ===================================
        # raise Exception(text_md['definitions'])
        # conanbuildinfo_file = self.getConanBuildInfo(build_dir_full_path)
        # if conanbuildinfo_file is None:
        #     raise FileNotFoundError("Unable to locate conanbuildinfo.json")
        #
        # with open(conanbuildinfo_file) as f:
        #     conan_build_info = json.loads(f.read())
        # for extension in build_ext_cmd.extensions:
        #     for dep in conan_build_info['dependencies']:
        #         extension.define_macros += [(d, None) for d in dep['defines']]

        # conanbuildinfo_file = self.getConanBuildInfo(build_dir_full_path)
        # if conanbuildinfo_file is None:
        #     raise FileNotFoundError("Unable to locate conanbuildinfo.json")
        #
        # self.announce(f"Reading from {conanbuildinfo_file}", 5)
        # with open(conanbuildinfo_file) as f:
        #     conan_build_info = json.loads(f.read())
        #
        # # for dep in conan_build_info['dependencies']:
        # #     if build_ext_cmd.compiler is not None:
        # #         build_ext_cmd.compiler.include_dirs = dep[
        # #                                          'include_paths'] + build_ext_cmd.compiler.include_dirs
        # #         build_ext_cmd.compiler.library_dirs = dep[
        # #                                          'lib_paths'] + build_ext_cmd.compiler.library_dirs
        # #         build_ext_cmd.compiler.libraries = dep['libs'] + build_ext_cmd.compiler.libraries
        # #         # build_ext_cmd.compiler.macros += [(d,) for d in dep['defines']]
        # #
        # #     else:
        # #         build_ext_cmd.include_dirs = dep['include_paths'] + build_ext_cmd.include_dirs
        # #         build_ext_cmd.library_dirs = dep['lib_paths'] + build_ext_cmd.library_dirs
        # #         build_ext_cmd.libraries = dep['libs'] + build_ext_cmd.libraries
        #
        # for extension in build_ext_cmd.extensions:
        #     # if "tesseract" in extension.libraries:
        #     #     extension.libraries.remove("tesseract")
        #
        #     for dep in conan_build_info['dependencies']:
        #         # new_include_dirs = dep['include_paths']
        #         new_include_dirs = [os.path.relpath(p, os.path.abspath(os.path.dirname(__file__))) for p in dep['include_paths']]
        #         extension.include_dirs = new_include_dirs + extension.include_dirs
        #         extension.library_dirs = dep['lib_paths'] + extension.library_dirs
        #         extension.libraries = dep['libs'] + extension.libraries
        #         extension.define_macros += [(d,) for d in dep['defines']]
        # d = self.reinitialize_command("build_ext")
        # print("")
        # conanbuildinfotext = os.path.join(build_dir, "conanbuildinfo.txt")
        # assert os.path.exists(conanbuildinfotext)
        #
        # text_md = self.get_from_txt(conanbuildinfotext)
        # for path in text_md['bin_paths']:
        #     if path not in build_ext_cmd.library_dirs:
        #         build_ext_cmd.library_dirs.insert(0, path)
        #
        # for extension in build_ext_cmd.extensions:
        #     for path in text_md['lib_paths']:
        #         if path not in extension.library_dirs:
        #             extension.library_dirs.insert(0, path)
        #
        #     for path in text_md['lib_paths']:
        #         if path not in extension.library_dirs:
        #             extension.library_dirs.insert(0, path)
        #
        # extension_deps = set()
        # all_libs = [lib.libraries for lib in build_ext_cmd.ext_map.values()]
        # for library_deps in all_libs:
        #     extension_deps = extension_deps.union(library_deps)
        #
        # for lib in text_md['libs']:
        #     if lib in build_ext_cmd.libraries:
        #         continue
        #
        #     if lib in extension_deps:
        #         continue
        #
        #     build_ext_cmd.libraries.insert(0, lib)

            #     for extension in build_ext_cmd.extensions:
            #         if "tesseract" in extension.libraries:
            #             extension.libraries.remove("tesseract")
            #
            #         for dep in conan_build_info['dependencies']:
            #             extension.include_dirs += dep['include_paths']
            #             extension.library_dirs += dep['lib_paths']
            #             extension.libraries += dep['libs']
            #             extension.define_macros += [(d,) for d in dep['defines']]

    # def run(self):
    #     build_ext_cmd = self.get_finalized_command("build_ext")
    #     build_dir = build_ext_cmd.build_temp
    #     if not os.path.exists(build_dir):
    #         os.makedirs(build_dir)
    #     build_dir_full_path = os.path.abspath(build_dir)
    #     install_command = [
    #         self.conan_exec,
    #         "install",
    #         "--build",
    #         "missing",
    #         "-if", build_dir_full_path,
    #         os.path.abspath(os.path.dirname(__file__))
    #     ]
    #
    #     subprocess.check_call(install_command, cwd=build_dir)
    #
    #     conanbuildinfo_file = self.getConanBuildInfo(build_dir_full_path)
    #     if conanbuildinfo_file is None:
    #         raise FileNotFoundError("Unable to locate conanbuildinfo.json")
    #
    #     self.announce(f"Reading from {conanbuildinfo_file}", 5)
    #     with open(conanbuildinfo_file) as f:
    #         conan_build_info = json.loads(f.read())
    #
    #     for extension in build_ext_cmd.extensions:
    #         if "tesseract" in extension.libraries:
    #             extension.libraries.remove("tesseract")
    #
    #         for dep in conan_build_info['dependencies']:
    #             extension.include_dirs += dep['include_paths']
    #             extension.library_dirs += dep['lib_paths']
    #             extension.libraries += dep['libs']
    #             extension.define_macros += [(d,) for d in dep['defines']]
