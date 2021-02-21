import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from builders.conan import BuildConan
from builders.pybind11 import PYBIND11_DEFAULT_URL
from builders.deps import parse_dumpbin_deps
import setuptools
from setuptools.command.build_ext import build_ext
import shutil
from distutils.version import StrictVersion
import tarfile
from urllib import request

PACKAGE_NAME = "uiucprescon.ocr"

if StrictVersion(setuptools.__version__) < StrictVersion('30.3'):
    print('your setuptools version does not support using setup.cfg. '
          'Upgrade setuptools and repeat the installation.',
          file=sys.stderr
          )

    sys.exit(1)

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

class BuildPybind11Extension(build_ext):
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
                    if dll is None:
                        raise FileNotFoundError("Mising for {}".format(dep))
                    shutil.copy(dll, dest)



tesseract_extension = setuptools.Extension(
    "uiucprescon.ocr.tesseractwrap",
    sources=[
        'uiucprescon/ocr/glue.cpp',
        'uiucprescon/ocr/reader.cpp',
        'uiucprescon/ocr/reader2.cpp',
        'uiucprescon/ocr/tesseractwrap.cpp',
        'uiucprescon/ocr/ImageLoaderStrategies.cpp',
        'uiucprescon/ocr/fileLoader.cpp',
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

#
# class ConanBuildInfoParser:
#     def __init__(self, fp):
#         self._fp = fp
#
#     def parse(self) -> Dict[str, List[str]]:
#         data = dict()
#         for subject_chunk in self.iter_subject_chunk():
#             subject_title = subject_chunk[0][1:-1]
#
#             data[subject_title] = subject_chunk[1:]
#         return data
#
#     def iter_subject_chunk(self) -> Iterable[Any]:
#         buffer = []
#         for line in self._fp:
#             line = line.strip()
#             if len(line) == 0:
#                 continue
#             if line.startswith("[") and line.endswith("]") and len(buffer) > 0:
#                 yield buffer
#                 buffer.clear()
#             buffer.append(line)
#         yield buffer
#         buffer.clear()


# class BuildConan(setuptools.Command):
#     user_options = [
#         ('conan-exec=', "c", 'conan executable'),
#         ('conan-cache=', None, 'conan cache directory')
#     ]
#
#     description = "Get the required dependencies from a Conan package manager"
#
#     def initialize_options(self):
#         self.conan_exec = None
#         self.conan_cache = None
#
#     def finalize_options(self):
#         if self.conan_exec is None:
#             self.conan_exec = shutil.which("conan")
#             if self.conan_exec is None:
#                 raise Exception("missing conan_exec")
#         if self.conan_cache is None:
#             build_ext_cmd = self.get_finalized_command("build_ext")
#             build_dir = build_ext_cmd.build_temp
#
#             self.conan_cache = \
#                 os.path.join(
#                     os.environ.get("CONAN_USER_HOME", build_dir),
#                     ".conan"
#                 )
#
#     def getConanBuildInfo(self, root_dir):
#         for root, dirs, files in os.walk(root_dir):
#             for f in files:
#                 if f == "conanbuildinfo.json":
#                     return os.path.join(root, f)
#         return None
#
#     def get_from_txt(self, conanbuildinfo_file):
#         definitions = []
#         include_paths = []
#         lib_paths = []
#         bin_paths = []
#         libs = []
#
#         with open(conanbuildinfo_file, "r") as f:
#             parser = builders.ConanBuildInfoParser(f)
#             data = parser.parse()
#             definitions = data['defines']
#             include_paths = data['includedirs']
#             lib_paths = data['libdirs']
#             bin_paths = data['bindirs']
#             libs = data['libs']
#
#         return {
#             "definitions": definitions,
#             "include_paths": list(include_paths),
#             "lib_paths": list(lib_paths),
#             "bin_paths": list(bin_paths),
#             "libs": list(libs),
#
#         }
#
#     def run(self):
#         # self.reinitialize_command("build_ext")
#         build_clib = self.get_finalized_command("build_clib")
#
#         build_dir = build_clib.build_temp
#
#         build_dir_full_path = os.path.abspath(build_dir)
#         conan_cache = self.conan_cache
#         self.mkpath(conan_cache)
#         self.mkpath(build_dir_full_path)
#         self.mkpath(os.path.join(build_dir_full_path, "lib"))
#         from conans.client import conan_api
#         self.announce(f"Using {conan_cache} for conan cache", 5)
#         conan = conan_api.Conan(cache_folder=os.path.abspath(conan_cache))
#         conan_options = []
#         build = ['missing']
#         settings = []
#
#         build_ext_cmd = self.get_finalized_command("build_ext")
#         if build_ext_cmd.debug is not None:
#             settings.append("build_type=Debug")
#
#         conan.install(
#             options=conan_options,
#             cwd=build_dir,
#             settings=settings,
#             build=build,
#             path=os.path.abspath(os.path.dirname(__file__)),
#             install_folder=build_dir_full_path
#         )
#
#         conanbuildinfotext = os.path.join(build_dir, "conanbuildinfo.txt")
#         assert os.path.exists(conanbuildinfotext)
#         text_md = self.get_from_txt(conanbuildinfotext)
#         for path in text_md['include_paths']:
#             if build_ext_cmd.compiler is None:
#                 if path not in build_ext_cmd.include_dirs:
#                     build_ext_cmd.include_dirs.insert(0, path)
#             else:
#                 build_ext_cmd.compiler.include_dirs.insert(0, path)
#
#         for path in text_md['lib_paths']:
#             assert os.path.exists(path)
#             if build_ext_cmd.compiler is None:
#                 if path not in build_ext_cmd.library_dirs:
#                     build_ext_cmd.library_dirs.insert(0, path)
#             else:
#                 build_ext_cmd.compiler.library_dirs.insert(0, path)
#
#         extension_deps = set()
#         for library_deps in [l.libraries for l in
#                              build_ext_cmd.ext_map.values()]:
#             extension_deps = extension_deps.union(library_deps)
#
#         for lib in text_md['libs']:
#             if lib == "tesseract":
#                 continue
#             if lib not in build_ext_cmd.libraries and lib not in extension_deps:
#                 if build_ext_cmd.compiler is None:
#                     build_ext_cmd.libraries.insert(0, lib)
#                 else:
#                     build_ext_cmd.compiler.libraries.insert(0, lib)
#         # ===================================
#         if build_ext_cmd.compiler is not None:
#             build_ext_cmd.compiler.macros += [(d, ) for d in text_md['definitions']]
#         else:
#             if hasattr(build_ext_cmd, "macros"):
#                 build_ext_cmd.macros += [(d, ) for d in text_md['definitions']]
#             else:
#                 build_ext_cmd.macros = [(d, ) for d in text_md['definitions']]
#         # ===================================
#         for extension in build_ext_cmd.extensions:
#             if "tesseract" in extension.libraries:
#                 extension.libraries.remove("tesseract")
#             for lib in text_md['libs']:
#                 if lib == "tesseract`":
#                     continue
#                 extension.libraries.append(lib)
#             extension.define_macros += [(d,) for d in text_md['definitions']]
#         # ===================================
#         # raise Exception(text_md['definitions'])
#         # conanbuildinfo_file = self.getConanBuildInfo(build_dir_full_path)
#         # if conanbuildinfo_file is None:
#         #     raise FileNotFoundError("Unable to locate conanbuildinfo.json")
#         #
#         # with open(conanbuildinfo_file) as f:
#         #     conan_build_info = json.loads(f.read())
#         # for extension in build_ext_cmd.extensions:
#         #     for dep in conan_build_info['dependencies']:
#         #         extension.define_macros += [(d, None) for d in dep['defines']]
#
#         # conanbuildinfo_file = self.getConanBuildInfo(build_dir_full_path)
#         # if conanbuildinfo_file is None:
#         #     raise FileNotFoundError("Unable to locate conanbuildinfo.json")
#         #
#         # self.announce(f"Reading from {conanbuildinfo_file}", 5)
#         # with open(conanbuildinfo_file) as f:
#         #     conan_build_info = json.loads(f.read())
#         #
#         # # for dep in conan_build_info['dependencies']:
#         # #     if build_ext_cmd.compiler is not None:
#         # #         build_ext_cmd.compiler.include_dirs = dep[
#         # #                                          'include_paths'] + build_ext_cmd.compiler.include_dirs
#         # #         build_ext_cmd.compiler.library_dirs = dep[
#         # #                                          'lib_paths'] + build_ext_cmd.compiler.library_dirs
#         # #         build_ext_cmd.compiler.libraries = dep['libs'] + build_ext_cmd.compiler.libraries
#         # #         # build_ext_cmd.compiler.macros += [(d,) for d in dep['defines']]
#         # #
#         # #     else:
#         # #         build_ext_cmd.include_dirs = dep['include_paths'] + build_ext_cmd.include_dirs
#         # #         build_ext_cmd.library_dirs = dep['lib_paths'] + build_ext_cmd.library_dirs
#         # #         build_ext_cmd.libraries = dep['libs'] + build_ext_cmd.libraries
#         #
#         # for extension in build_ext_cmd.extensions:
#         #     # if "tesseract" in extension.libraries:
#         #     #     extension.libraries.remove("tesseract")
#         #
#         #     for dep in conan_build_info['dependencies']:
#         #         # new_include_dirs = dep['include_paths']
#         #         new_include_dirs = [os.path.relpath(p, os.path.abspath(os.path.dirname(__file__))) for p in dep['include_paths']]
#         #         extension.include_dirs = new_include_dirs + extension.include_dirs
#         #         extension.library_dirs = dep['lib_paths'] + extension.library_dirs
#         #         extension.libraries = dep['libs'] + extension.libraries
#         #         extension.define_macros += [(d,) for d in dep['defines']]
#         # d = self.reinitialize_command("build_ext")
#         # print("")
#         # conanbuildinfotext = os.path.join(build_dir, "conanbuildinfo.txt")
#         # assert os.path.exists(conanbuildinfotext)
#         #
#         # text_md = self.get_from_txt(conanbuildinfotext)
#         # for path in text_md['bin_paths']:
#         #     if path not in build_ext_cmd.library_dirs:
#         #         build_ext_cmd.library_dirs.insert(0, path)
#         #
#         # for extension in build_ext_cmd.extensions:
#         #     for path in text_md['lib_paths']:
#         #         if path not in extension.library_dirs:
#         #             extension.library_dirs.insert(0, path)
#         #
#         #     for path in text_md['lib_paths']:
#         #         if path not in extension.library_dirs:
#         #             extension.library_dirs.insert(0, path)
#         #
#         # extension_deps = set()
#         # all_libs = [lib.libraries for lib in build_ext_cmd.ext_map.values()]
#         # for library_deps in all_libs:
#         #     extension_deps = extension_deps.union(library_deps)
#         #
#         # for lib in text_md['libs']:
#         #     if lib in build_ext_cmd.libraries:
#         #         continue
#         #
#         #     if lib in extension_deps:
#         #         continue
#         #
#         #     build_ext_cmd.libraries.insert(0, lib)
#
#             #     for extension in build_ext_cmd.extensions:
#             #         if "tesseract" in extension.libraries:
#             #             extension.libraries.remove("tesseract")
#             #
#             #         for dep in conan_build_info['dependencies']:
#             #             extension.include_dirs += dep['include_paths']
#             #             extension.library_dirs += dep['lib_paths']
#             #             extension.libraries += dep['libs']
#             #             extension.define_macros += [(d,) for d in dep['defines']]
#
#     # def run(self):
#     #     build_ext_cmd = self.get_finalized_command("build_ext")
#     #     build_dir = build_ext_cmd.build_temp
#     #     if not os.path.exists(build_dir):
#     #         os.makedirs(build_dir)
#     #     build_dir_full_path = os.path.abspath(build_dir)
#     #     install_command = [
#     #         self.conan_exec,
#     #         "install",
#     #         "--build",
#     #         "missing",
#     #         "-if", build_dir_full_path,
#     #         os.path.abspath(os.path.dirname(__file__))
#     #     ]
#     #
#     #     subprocess.check_call(install_command, cwd=build_dir)
#     #
#     #     conanbuildinfo_file = self.getConanBuildInfo(build_dir_full_path)
#     #     if conanbuildinfo_file is None:
#     #         raise FileNotFoundError("Unable to locate conanbuildinfo.json")
#     #
#     #     self.announce(f"Reading from {conanbuildinfo_file}", 5)
#     #     with open(conanbuildinfo_file) as f:
#     #         conan_build_info = json.loads(f.read())
#     #
#     #     for extension in build_ext_cmd.extensions:
#     #         if "tesseract" in extension.libraries:
#     #             extension.libraries.remove("tesseract")
#     #
#     #         for dep in conan_build_info['dependencies']:
#     #             extension.include_dirs += dep['include_paths']
#     #             extension.library_dirs += dep['lib_paths']
#     #             extension.libraries += dep['libs']
#     #             extension.define_macros += [(d,) for d in dep['defines']]


setuptools.setup(
    packages=['uiucprescon.ocr'],
    setup_requires=[
        'pytest-runner'
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
    cmdclass={
        "build_ext": BuildTesseractExt,
        "build_conan": BuildConan
        # "build_ext": BuildTesseract,
    },
)
