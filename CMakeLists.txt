cmake_minimum_required(VERSION 3.15)
project(ocr)
#find_package(PythonInterp)
#find_package(PythonLibs)
#find_package(Python3 REQUIRED COMPONENTS Development)

#set(output_dir ${CMAKE_BINARY_DIR}/uiucprescon/ocr)
#set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${output_dir})
set(CMAKE_INSTALL_OPENMP_LIBRARIES TRUE)
set(CMAKE_INSTALL_SYSTEM_RUNTIME_DESTINATION uiucprescon/ocr/tesseract/bin)
include(InstallRequiredSystemLibraries)
find_package(Tesseract REQUIRED)
find_package(Catch2)

set(CMAKE_CXX_STANDARD 17)
# If google isn't going to make importable targets, then I am
if(NOT TARGET Tesseract::Tesseract)
    add_library(Tesseract::Tesseract INTERFACE IMPORTED )
    set_target_properties(Tesseract::Tesseract PROPERTIES
        INTERFACE_INCLUDE_DIRECTORIES "${tesseract_INCLUDE_DIRS}"
        INTERFACE_LINK_LIBRARIES "${Tesseract_LIBRARIES}"
         INTERFACE_COMPILE_DEFINITIONS "${tesseract_COMPILE_DEFINITIONS}"
        )
#    Tesseract_LIBRARIES
endif(NOT TARGET Tesseract::Tesseract)

find_package(Leptonica REQUIRED)
include(FetchContent)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
FetchContent_Declare(libpybind11
        URL https://github.com/pybind/pybind11/archive/refs/tags/v2.13.6.tar.gz
        URL_HASH SHA1=8c7e3e8fec829ced31a495dec281153511f33c63
        DOWNLOAD_EXTRACT_TIMESTAMP true
        )

FetchContent_GetProperties(libpybind11)
if (NOT libpybind11_POPULATED)
    FetchContent_MakeAvailable(libpybind11)
endif ()

add_subdirectory(src/uiucprescon/ocr)
include(CTest)
add_subdirectory(tests)