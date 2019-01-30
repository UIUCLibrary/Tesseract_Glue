cmake_minimum_required(VERSION 3.12)
project(ocr)
#find_package(Python3 REQUIRED COMPONENTS Development)
find_package(PythonInterp)
find_package(PythonLibs)
#message(STATUS "Python3_ROOT_DIR = ${Python3_ROOT_DIR}")
#message(FATAL "Python3_RUNTIME_LIBRARY_DIRS = ${Python3_RUNTIME_LIBRARY_DIRS}")
set(output_dir ${CMAKE_BINARY_DIR}/uiucprescon/ocr)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${output_dir})

#find_package(CPPAN REQUIRED)
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
include(ExternalProject)
#==============================
FetchContent_Declare(googletest
        URL https://github.com/google/googletest/archive/release-1.8.1.tar.gz
##        URL_HASH SHA1=0acaeb967f09dbef53a1e2a4366780548597beba
        )
##
FetchContent_GetProperties(googletest)
if (NOT googletest_POPULATED)
    FetchContent_Populate(googletest)
endif ()
#==============================

ExternalProject_Add(leptonica
        URL https://github.com/DanBloomberg/leptonica/archive/1.77.0.tar.gz
        CMAKE_ARGS
        -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR>
        )
ExternalProject_Get_Property(leptonica INSTALL_DIR)
set(leptonica_INSTALL_DIR ${INSTALL_DIR})
add_library(libleptonica UNKNOWN IMPORTED)
set_target_properties(libleptonica PROPERTIES
        INCLUDE_DIRECTORIES ${INSTALL_DIR}/include
#        INTERFACE_INCLUDE_DIRECTORIES ${INSTALL_DIR}/include
        #        INCLUDE_DIRECTORIES ${INSTALL_DIR}/include/tesseract
        #        IMPORTED_LOCATION_DEBUG ${INSTALL_DIR}/lib/${CMAKE_STATIC_LIBRARY_PREFIX}tesseract40d${CMAKE_STATIC_LIBRARY_SUFFIX}
        #        IMPORTED_LOCATION_RELEASE ${INSTALL_DIR}/lib/${CMAKE_STATIC_LIBRARY_PREFIX}tesseract40${CMAKE_STATIC_LIBRARY_SUFFIX}
        #        CXX_STANDARD 98
        )
add_dependencies(libleptonica leptonica)
unset(INSTALL_DIR)
#==============================
ExternalProject_Add(tesseract
        URL https://github.com/tesseract-ocr/tesseract/archive/4.0.0.tar.gz
        UPDATE_COMMAND
        ${CMAKE_COMMAND} -E copy_directory  "${googletest_SOURCE_DIR}" "<SOURCE_DIR>/googletest/"
        CMAKE_ARGS
            -DLeptonica_DIR:PATH=${leptonica_INSTALL_DIR}/cmake
            -DCMAKE_INSTALL_PREFIX:PATH=<INSTALL_DIR>
            -DBUILD_TESTS:BOOL=ON
            -Dgtest_force_shared_crt:BOOL=ON
#        INSTALL_COMMAND ""

        TEST_COMMAND <BINARY_DIR>/bin/tesseract_tests
        #        BUILD_COMMAND ""
        DEPENDS leptonica
        )
ExternalProject_Get_Property(tesseract INSTALL_DIR)
add_library(libtesseract UNKNOWN IMPORTED)
set_target_properties(libtesseract PROPERTIES
#        INTERFACE_INCLUDE_DIRECTORIES ${INSTALL_DIR}/include
        INCLUDE_DIRECTORIES ${INSTALL_DIR}/include/tesseract
        IMPORTED_LOCATION_DEBUG ${INSTALL_DIR}/lib/${CMAKE_STATIC_LIBRARY_PREFIX}tesseract40d${CMAKE_STATIC_LIBRARY_SUFFIX}
        IMPORTED_LOCATION_RELEASE ${INSTALL_DIR}/lib/${CMAKE_STATIC_LIBRARY_PREFIX}tesseract40${CMAKE_STATIC_LIBRARY_SUFFIX}
#        CXX_STANDARD 98
        )


#add_custom_target(dummy COMMAND ${CMAKE_COMMAND} -E echo "ASDFasdf $<TARGET_FILE:tesseract>")
add_dependencies(tesseract libtesseract)
add_subdirectory(uiucprescon/ocr)
#include(CTest)
add_subdirectory(tests)