# Build dependencies

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
        )
execute_process(COMMAND ${CMAKE_COMMAND} -S ${CMAKE_BINARY_DIR}/zlib-src -B ${CMAKE_BINARY_DIR}/zlib-build -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/zlib)
execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/zlib-build --config ${Config} --target install -j 8)


# ======================
# leptonica
# ======================
FetchContent_Populate(leptonica
    URL https://github.com/DanBloomberg/leptonica/archive/1.77.0.tar.gz
        )
execute_process(COMMAND ${CMAKE_COMMAND} -S ${CMAKE_BINARY_DIR}/leptonica-src -B ${CMAKE_BINARY_DIR}/leptonica-build -DZLIB_ROOT:PATH=${CMAKE_BINARY_DIR}/zlib -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/leptonica)
execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/leptonica-build --config ${Config} --target install -j 8)

# ======================
# tesseract
# ======================
FetchContent_Populate(tesseract
        URL https://github.com/tesseract-ocr/tesseract/archive/4.0.0.tar.gz
        )

FetchContent_Populate(googletest
        URL https://github.com/google/googletest/archive/release-1.8.1.tar.gz
        SOURCE_DIR ${CMAKE_BINARY_DIR}/tesseract-src/googletest
        )

execute_process(COMMAND ${CMAKE_COMMAND} -S ${CMAKE_BINARY_DIR}/tesseract-src -B ${CMAKE_BINARY_DIR}/tesseract-build -DBUILD_TRAINING_TOOLS:BOOL=OFF -DLeptonica_DIR:PATH=${CMAKE_BINARY_DIR}/leptonica -DBUILD_TESTS:BOOL=ON -Dgtest_force_shared_crt:BOOL=ON -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_BINARY_DIR}/tesseract)
execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/tesseract-build --config ${Config} -j 8)

find_program(tesseract_tests_exec tesseract_tests
        PATHS
            ${CMAKE_BINARY_DIR}/tesseract-build/bin/Debug
            ${CMAKE_BINARY_DIR}/tesseract-build/bin/release
        )
if(NOT tesseract_tests_exec)
    message(FATAL_ERROR "Tesseract did not build tests")
endif()
execute_process(COMMAND ${tesseract_tests_exec} RESULT_VARIABLE TESSERACT_TESTS)
if(NOT TESSERACT_TESTS EQUAL 0)
    message(FATAL_ERROR "Tesseract did not pass self tests")
endif()

execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/tesseract-build --target install --config ${Config} -j 8)
