cmake_minimum_required(VERSION 3.12)
project(ocr)
#find_package(Python3 REQUIRED COMPONENTS Development)
find_package(PythonInterp)
find_package(PythonLibs)
#message(STATUS "Python3_ROOT_DIR = ${Python3_ROOT_DIR}")
#message(FATAL "Python3_RUNTIME_LIBRARY_DIRS = ${Python3_RUNTIME_LIBRARY_DIRS}")
set(output_dir ${CMAKE_BINARY_DIR}/uiucprescon/ocr)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${output_dir})

find_package(CPPAN REQUIRED)
include(FetchContent)

FetchContent_Declare(libpybind11
        URL https://github.com/pybind/pybind11/archive/v2.2.3.tar.gz
        URL_HASH SHA1=0acaeb967f09dbef53a1e2a4366780548597beba
        )

FetchContent_GetProperties(libpybind11)
if (NOT libpybind11_POPULATED)
    FetchContent_Populate(libpybind11)
#    option(BUILD_examples "" OFF)
#    option(BUILD_shared "" OFF)
#    option(BUILD_tests "" NO)
#    option(BUILD_tools "" NO)

    add_subdirectory(${libpybind11_SOURCE_DIR} ${libpybind11_BINARY_DIR})
endif ()

add_subdirectory(uiucprescon/ocr)
include(CTest)
add_subdirectory(tests)