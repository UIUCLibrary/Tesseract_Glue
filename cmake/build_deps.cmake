# Build dependencies
if(NOT CMAKE_GENERATOR)
        message(FATAL_ERROR "Required variable not set, CMAKE_GENERATOR")
endif()

include(FetchContent)

message("Hello")

if(NOT Config)
    set(Config release)
endif()

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
# libpng
# ======================
FetchContent_Populate(libpng
        URL https://download.sourceforge.net/libpng/libpng-1.6.36.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/libpng-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/libpng-build
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/libpng
        URL_HASH   SHA256=ca13c548bde5fb6ff7117cc0bdab38808acb699c0eccb613f0e4697826e1fd7d  
        )
execute_process(COMMAND ${CMAKE_COMMAND} -G ${CMAKE_GENERATOR}
        -S ${CMAKE_BINARY_DIR}/source/libpng-src -B ${CMAKE_BINARY_DIR}/build/libpng-build
        #        -DZLIB_INCLUDE_DIR:PATH=${CMAKE_BINARY_DIR}/dist/include
        #        -DZLIB_LIBRARY_RELEASE:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlib.lib
        #        -DZLIB_LIBRARY_DEBUG:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlibd.lib
        #         -DTIFF_INCLUDE_DIR:FILEPATH=${TIFF_INCLUDE_DIR}
        #         -DTIFF_LIBRARY_RELEASE:FILEPATH=${TIFF_LIBRARY}
        -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/dist
        -DCMAKE_MODULE_PATH=${CMAKE_BINARY_DIR}/dist/cmake
        -DCMAKE_BUILD_TYPE=${Config}
        )       
execute_process(COMMAND 
        ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/libpng-build --config ${Config} --target install -j 8)

find_path(PNG_PNG_INCLUDE_DIR
        NAMES png.h
        PATHS ${CMAKE_BINARY_DIR}/dist/include
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )

find_library(PNG_LIBRARY_RELEASE
        NAMES
            libpng16.lib
        PATHS 
            ${CMAKE_BINARY_DIR}/dist/lib
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )
       

# ======================
# libJPEG
# ======================
FetchContent_Populate(libJPEG
        URL https://github.com/libjpeg-turbo/libjpeg-turbo/archive/2.0.1.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/libjpeg-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/libjpeg-build
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/libjpeg-build
#        URL_HASH   MD5=114192d7ebe537912a2b97408832e7fd
        )

execute_process(COMMAND ${CMAKE_COMMAND} -G ${CMAKE_GENERATOR}
        -S ${CMAKE_BINARY_DIR}/source/libjpeg-src -B ${CMAKE_BINARY_DIR}/build/libjpeg-build
#        -DZLIB_INCLUDE_DIR:PATH=${CMAKE_BINARY_DIR}/dist/include
#        -DZLIB_LIBRARY_RELEASE:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlib.lib
#        -DZLIB_LIBRARY_DEBUG:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlibd.lib
#         -DTIFF_INCLUDE_DIR:FILEPATH=${TIFF_INCLUDE_DIR}
#         -DTIFF_LIBRARY_RELEASE:FILEPATH=${TIFF_LIBRARY}
        -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/dist
        -DCMAKE_MODULE_PATH=${CMAKE_BINARY_DIR}/dist/cmake
        -DCMAKE_BUILD_TYPE=${Config}
        )
        
execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/libjpeg-build --config ${Config} --target install -j 8)

find_path(JPEG_INCLUDE_DIR
        NAMES jpeglib.h
        PATHS ${CMAKE_BINARY_DIR}/dist/include
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )

find_library(JPEG_LIBRARY
        NAMES
            jpeg.lib
#            tiff.lib
        PATHS ${CMAKE_BINARY_DIR}/dist/lib
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )


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
        -DJPEG_INCLUDE_DIR=${JPEG_INCLUDE_DIR}
        -DJPEG_LIBRARY=${JPEG_LIBRARY}
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

# message(FATAL_ERROR "Done")

# ======================
# OpenJPEG
# ======================
FetchContent_Populate(openjpeg
        URL https://github.com/uclouvain/openjpeg/archive/v2.3.0.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/openjpeg-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/openjpeg-build
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/openjpeg-build
#        URL_HASH   MD5=114192d7ebe537912a2b97408832e7fd
        )
# message("PNG_LIBRARY_RELEASE = ${PNG_LIBRARY_RELEASE}")
# message("PNG_PNG_INCLUDE_DIR = ${PNG_PNG_INCLUDE_DIR}")
execute_process(COMMAND ${CMAKE_COMMAND} -G ${CMAKE_GENERATOR}
        -S ${CMAKE_BINARY_DIR}/source/openjpeg-src -B ${CMAKE_BINARY_DIR}/build/openjpeg-build
       -DZLIB_INCLUDE_DIR:PATH=${CMAKE_BINARY_DIR}/dist/include
       -DZLIB_LIBRARY_RELEASE:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlib.lib
       -DZLIB_LIBRARY_DEBUG:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlibd.lib
       -DPNG_LIBRARY_RELEASE:FILEPATH=${PNG_LIBRARY_RELEASE}
       -DPNG_PNG_INCLUDE_DIR:PATH=${PNG_PNG_INCLUDE_DIR}
         
        -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/dist
        -DCMAKE_MODULE_PATH=${CMAKE_BINARY_DIR}/dist/cmake
        -DCMAKE_BUILD_TYPE=${Config}
        )

execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/openjpeg-build --config ${Config} --target install -j 8)

find_path(OPENJPEG_INCLUDE_DIR
        NAMES openjpeg-2.3/openjpeg.h
        PATHS ${CMAKE_BINARY_DIR}/dist/include
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )

find_library(OPENJPEG_LIBRARY
        NAMES
             openjp2.lib
#            tiff.lib
        PATHS ${CMAKE_BINARY_DIR}/dist/lib
        NO_DEFAULT_PATH
        NO_CMAKE_PATH
        NO_CMAKE_SYSTEM_PATH
        )
# message("OPENJPEG_INCLUDE_DIR = ${OPENJPEG_INCLUDE_DIR}")
# message("OPENJPEG_LIBRARY = ${OPENJPEG_LIBRARY}")



# ======================
# leptonica
# ======================

FetchContent_Populate(leptonica
    URL https://github.com/DanBloomberg/leptonica/archive/1.77.0.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/source/leptonica-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/build/leptonica-build
        SUBBUILD_DIR ${CMAKE_BINARY_DIR}/subbuild/leptonica
        URL_HASH   MD5=839e4f4657f32d4a94d6eeee13b0acd5
        )

execute_process(
        COMMAND
                ${CMAKE_COMMAND} -G ${CMAKE_GENERATOR}
                -S ${CMAKE_BINARY_DIR}/source/leptonica-src -B ${CMAKE_BINARY_DIR}/build/leptonica-build
                -DZLIB_INCLUDE_DIR:PATH=${CMAKE_BINARY_DIR}/dist/include
                -DZLIB_LIBRARY_RELEASE:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlib.lib
                -DZLIB_LIBRARY_DEBUG:FILEPATH=${CMAKE_BINARY_DIR}/dist/lib/zlibd.lib
                -DTIFF_INCLUDE_DIR:PATH=${TIFF_INCLUDE_DIR}
                -DTIFF_LIBRARY:FILEPATH=${TIFF_LIBRARY}
                -DJPEG_INCLUDE_DIR=${JPEG_INCLUDE_DIR}
                -DJPEG_LIBRARY=${JPEG_LIBRARY}
                # -DPNG_DIR:PATH=${CMAKE_BINARY_DIR}/dist
                # -DOPENJPEG_INCLUDE_DIR=${OPENJPEG_INCLUDE_DIR}
                # -DOPENJPEG_LIBRARY=${OPENJPEG_LIBRARY}
                -DCMAKE_BUILD_TYPE=${Config}
                -DCMAKE_PREFIX_PATH=${CMAKE_BINARY_DIR}/dist/
                -DCMAKE_MODULE_PATH=${CMAKE_BINARY_DIR}/dist/cmake
                -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/dist
                # -DCMAKE_INCLUDE_PATH:PATH=${CMAKE_BINARY_DIR}/dist/include
        # WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/dist/include
        )
# message(FATAL_ERROR "Done")
execute_process(
        COMMAND 
                ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/build/leptonica-build --config ${Config} --target install -j 8
        # WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/dist/include
        )
# message(FATAL_ERROR "Stop now ")
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
