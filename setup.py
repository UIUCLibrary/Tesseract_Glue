import json
import os
import sys
from pprint import pprint
from typing import List, Literal, Union, Dict, Optional, Tuple
import setuptools
from pybind11.setup_helpers import Pybind11Extension
from uiucprescon.build import introspection
from uiucprescon.build.conan.utils import LanguageStandardsVersion
from uiucprescon.build.pybind11_builder import BuildPybind11Extension

PACKAGE_NAME = "uiucprescon.ocr"

def get_mini_required_std(
    extensions: List[Dict[str, str]],
    standard=Union[Literal["c_std"], Literal["cxx_std"]]
) -> Optional[str]:

    required_std = None
    for ext in extensions:
        if standard in ext:
            if required_std is None:
                required_std = ext[standard]
            else:
                if int(required_std) < int(ext[standard]):
                    required_std = ext[standard]
    return required_std

class BuildTesseractExt(BuildPybind11Extension):

    def get_compiler_definitions(self) -> List[Tuple[str, str]]:
        if sys.platform != "linux":
            return []
        build_conan = self.get_finalized_command("build_conan")
        conan_build_info =\
            os.path.join(build_conan.build_temp, "conan_build_info.json")

        with open(conan_build_info) as fp:
            data = json.loads(fp.read())
            for node in data['graph']['nodes'].values():
                if node.get('name') != "tesseract":
                    continue
                # The std::string type needs to matche libstdc++ or libstdc++11
                lib_cxx = node['settings'].get('compiler.libcxx')
                return [
                    (
                        "_GLIBCXX_USE_CXX11_ABI",
                        "0" if lib_cxx == 'libstdc++' else "1"
                    ),
                ]
        return []

    def build_extension(self, ext: Pybind11Extension):
        if not self.dry_run:
            build_conan = self.get_finalized_command("build_conan")
            build_conan.build_libs = ['missing']
            required_cxx_std = get_mini_required_std(
                introspection.get_extension_build_info()["extensions"],
                standard="cxx_std"
            )

            if required_cxx_std:
                build_conan.language_standards =\
                    LanguageStandardsVersion(cpp_std=required_cxx_std)
            build_conan.run()
        ext.define_macros.extend(self.get_compiler_definitions())
        super().build_extension(ext)


tesseract_extension = Pybind11Extension(
    "uiucprescon.ocr.tesseractwrap",
    sources=[
        'src/uiucprescon/ocr/Capabilities.cpp',
        'src/uiucprescon/ocr/glue.cpp',
        'src/uiucprescon/ocr/reader.cpp',
        'src/uiucprescon/ocr/reader2.cpp',
        'src/uiucprescon/ocr/tesseractwrap.cpp',
        'src/uiucprescon/ocr/Image.cpp',
        'src/uiucprescon/ocr/ImageLoaderStrategies.cpp',
        'src/uiucprescon/ocr/fileLoader.cpp',
        'src/uiucprescon/ocr/glueExceptions.cpp',
        'src/uiucprescon/ocr/utils.cpp',
    ],
    libraries=[
        "tesseract",
        'leptonica',
      ]
      # this is an issue with conan not seeing that libarchive requires
      # Advapi32 on windows
      + (["Advapi32"] if sys.platform == 'win32' else []),
    language='c++',
    cxx_std=17
)

tesseract_extension.cmake_source_dir = \
    os.path.abspath(os.path.dirname(__file__))

setuptools.setup(
    ext_modules=[
        tesseract_extension
    ],
    cmdclass={
        "build_ext": BuildTesseractExt,
    }
)
