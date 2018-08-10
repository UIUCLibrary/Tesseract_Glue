cmake_minimum_required(VERSION 3.12)
project(ocr)
find_package(Python3 REQUIRED COMPONENTS Development)
#message(STATUS "Python3_ROOT_DIR = ${Python3_ROOT_DIR}")
#message(FATAL "Python3_RUNTIME_LIBRARY_DIRS = ${Python3_RUNTIME_LIBRARY_DIRS}")
set(output_dir ${CMAKE_BINARY_DIR}/ocr)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${output_dir})

find_package(CPPAN REQUIRED)
include(FetchContent)

FetchContent_Declare(libpybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
#        GIT_TAG 8edc147
        GIT_TAG f7bc18f528bb35cd06c93d0a58c17e6eea3fa68c
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

add_subdirectory(ocr)
include(CTest)
add_subdirectory(tests)