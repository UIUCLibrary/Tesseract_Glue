# Build dependencies

include(FetchContent)
message("Hello")
if(NOT Config)
    set(Config release)
endif()
#message(FATAL_ERROR "CMAKE_GENERATOR = ${CMAKE_GENERATOR}")

# ======================
# ZLIB
# ======================
FetchContent_Populate(zlib
        URL https://www.zlib.net/zlib-1.2.11.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/zlib-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/zlib-build
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/zlib-subbuild
        URL_HASH   MD5=1c9f62f0778697a09d36121ead88e08e
        )

execute_process(COMMAND ${CMAKE_COMMAND}
        -G ${CMAKE_GENERATOR}
        -S ${CMAKE_BINARY_DIR}/source/zlib-src -B ${CMAKE_BINARY_DIR}/build/zlib-build
        -DCMAKE_BUILD_TYPE=${Config}
        -DCMAKE_MODULE_PATH=${CMAKE_BINARY_DIR}/dist/cmake
        -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/dist)

execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/zlib-build --config ${Config} --target install -j 8)


# ======================
# libtiff
# ======================
FetchContent_Populate(libtiff
        URL https://download.osgeo.org/libtiff/tiff-4.0.10.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/libtiff-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/libtiff-build
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/libtiff-build
        URL_HASH   MD5=114192d7ebe537912a2b97408832e7fd
        )

execute_process(COMMAND ${CMAKE_COMMAND} -G ${CMAKE_GENERATOR}
        -S ${CMAKE_BINARY_DIR}/source/libtiff-src -B ${CMAKE_BINARY_DIR}/build/libtiff-build
        -DZLIB_INCLUDE_DIR:PATH=${CMAKE_BINARY_DIR}/dist/include
        -DZLIB_LIBRARY_RELEASE:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlib.lib
        -DZLIB_LIBRARY_DEBUG:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlibd.lib
        -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/dist
        -DCMAKE_MODULE_PATH=${CMAKE_BINARY_DIR}/dist/cmake
        -DCMAKE_BUILD_TYPE=${Config}
        )

execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/libtiff-build --config ${Config} --target install -j 8)
find_path(TIFF_INCLUDE_DIR
        NAMES tiff.h
        PATHS ${CMAKE_BINARY_DIR}/dist/include
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )

find_library(TIFF_LIBRARY
        NAMES
            tiff
            tiff.lib
        PATHS ${CMAKE_BINARY_DIR}/dist/lib
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )


# ======================
# OpenJPEG
# ======================
FetchContent_Populate(libtiff
        URL https://github.com/uclouvain/openjpeg/archive/v2.3.0.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/openjpeg-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/openjpeg-build
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/openjpeg-build
#        URL_HASH   MD5=114192d7ebe537912a2b97408832e7fd
        )

execute_process(COMMAND ${CMAKE_COMMAND} -G ${CMAKE_GENERATOR}
        -S ${CMAKE_BINARY_DIR}/source/openjpeg-src -B ${CMAKE_BINARY_DIR}/build/openjpeg-build
#        -DZLIB_INCLUDE_DIR:PATH=${CMAKE_BINARY_DIR}/dist/include
#        -DZLIB_LIBRARY_RELEASE:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlib.lib
#        -DZLIB_LIBRARY_DEBUG:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlibd.lib
        -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/dist
        -DCMAKE_MODULE_PATH=${CMAKE_BINARY_DIR}/dist/cmake
        -DCMAKE_BUILD_TYPE=${Config}
        )

execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/openjpeg-build --config ${Config} --target install -j 8)
find_path(JPEG_INCLUDE_DIR
        NAMES openjpeg-2.3/openjpeg.h
        PATHS ${CMAKE_BINARY_DIR}/dist/include
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )

find_library(JPEG_LIBRARY
        NAMES
            openjp2.lib
#            tiff.lib
        PATHS ${CMAKE_BINARY_DIR}/dist/lib
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )

# ======================
# libpng
# ======================

# TODO: install libpng

# ======================
# leptonica
# ======================

FetchContent_Populate(leptonica
    URL https://github.com/DanBloomberg/leptonica/archive/1.77.0.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/leptonica-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/leptonica-build
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/leptonica-build
        URL_HASH   MD5=839e4f4657f32d4a94d6eeee13b0acd5
        )

execute_process(COMMAND
        ${CMAKE_COMMAND} -G ${CMAKE_GENERATOR}
        -S ${CMAKE_BINARY_DIR}/source/leptonica-src -B ${CMAKE_BINARY_DIR}/build/leptonica-build
        -DZLIB_INCLUDE_DIR:PATH=${CMAKE_BINARY_DIR}/dist/include
        -DZLIB_LIBRARY_RELEASE:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlib.lib
        -DZLIB_LIBRARY_DEBUG:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlibd.lib
        -DTIFF_INCLUDE_DIR:PATH=${TIFF_INCLUDE_DIR}
        -DTIFF_LIBRARY:FILEPATH=${TIFF_LIBRARY}
        -DJPEG_INCLUDE_DIR=${JPEG_INCLUDE_DIR}
        -DJPEG_LIBRARY=${JPEG_LIBRARY}
        -DCMAKE_BUILD_TYPE=${Config}
        -DCMAKE_MODULE_PATH=${CMAKE_BINARY_DIR}/dist/cmake
        -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/dist)

execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/leptonica-build --config ${Config} --target install -j 8)
# ======================
# tesseract
# ======================
FetchContent_Populate(tesseract
        URL https://github.com/tesseract-ocr/tesseract/archive/4.0.0.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/tesseract-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/tesseract-build
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/tesseract-build
        URL_HASH   MD5=ebed139edb16f10c5ba6ee3bf38f7dc5
        )

FetchContent_Populate(googletest
        URL https://github.com/google/googletest/archive/release-1.8.1.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/tesseract-src/googletest
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/googletest
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/googletest
        URL_HASH   MD5=2e6fbeb6a91310a16efe181886c59596
        )

execute_process(COMMAND ${CMAKE_COMMAND} -G ${CMAKE_GENERATOR}
        -S ${CMAKE_BINARY_DIR}/source/tesseract-src -B ${CMAKE_BINARY_DIR}/build/tesseract-build
        -DBUILD_TRAINING_TOOLS:BOOL=OFF
        -DBUILD_TESTS:BOOL=ON
        -Dgtest_force_shared_crt:BOOL=ON
        -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/dist
        -DCMAKE_MODULE_PATH=${CMAKE_BINARY_DIR}/dist/cmake
        -DCMAKE_BUILD_TYPE=${Config}
    )
execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/tesseract-build --config ${Config} -j 8)

find_program(tesseract_tests_exec tesseract_tests
        PATHS
            ${CMAKE_BINARY_DIR}/build/tesseract-build/bin/
            ${CMAKE_BINARY_DIR}/build/tesseract-build/bin/Debug
            ${CMAKE_BINARY_DIR}/build/tesseract-build/bin/release
        )
if(NOT tesseract_tests_exec)
    message(FATAL_ERROR "Tesseract did not build tests")
endif()
execute_process(COMMAND ${tesseract_tests_exec} RESULT_VARIABLE TESSERACT_TESTS)
if(NOT TESSERACT_TESTS EQUAL 0)
    message(FATAL_ERROR "Tesseract did not pass self tests")
endif()

execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/tesseract-build --target install --config ${Config} -j 8)
