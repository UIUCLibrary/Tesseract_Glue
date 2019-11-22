cmake_minimum_required(VERSION 3.15)
project(ocr)
#find_package(PythonInterp)
#find_package(PythonLibs)
#find_package(Python3 REQUIRED COMPONENTS Development)

#set(output_dir ${CMAKE_BINARY_DIR}/uiucprescon/ocr)
#set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${output_dir})
include(InstallRequiredSystemLibraries)
find_package(Tesseract REQUIRED)

# If google isn't going to make importable targets, then I am
if(NOT TARGET tesseract::tesseract)
    add_library(tesseract::tesseract INTERFACE IMPORTED )
    set_target_properties(tesseract::tesseract PROPERTIES
        INTERFACE_INCLUDE_DIRECTORIES "${tesseract_INCLUDE_DIRS}"
        INTERFACE_LINK_LIBRARIES "${Tesseract_LIBRARIES}"
         INTERFACE_COMPILE_DEFINITIONS "${tesseract_COMPILE_DEFINITIONS}"
        )
#    Tesseract_LIBRARIES
endif(NOT TARGET tesseract::tesseract)

find_package(Leptonica REQUIRED)
include(FetchContent)

FetchContent_Declare(libpybind11
        URL https://github.com/pybind/pybind11/archive/v2.2.3.tar.gz
        URL_HASH SHA1=0acaeb967f09dbef53a1e2a4366780548597beba
        )

FetchContent_GetProperties(libpybind11)
if (NOT libpybind11_POPULATED)
    FetchContent_Populate(libpybind11)

    add_subdirectory(${libpybind11_SOURCE_DIR} ${libpybind11_BINARY_DIR})
endif ()

add_subdirectory(uiucprescon/ocr)
include(CTest)
add_subdirectory(tests)