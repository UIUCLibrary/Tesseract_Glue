cmake_minimum_required(VERSION 3.12)
project(ocr)
find_package(Python3 REQUIRED COMPONENTS Development)
set(output_dir ${CMAKE_BINARY_DIR}/ocr)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${output_dir})

find_package(CPPAN REQUIRED)
add_subdirectory(ocr)
#cppan_add_package(
#    pvt.cppan.demo.google.tesseract.libtesseract
#    pvt.cppan.demo.danbloomberg.leptonica
#)
#cppan_execute()
#Python3_add_library(tesseractwrap MODULE hello.cpp)
#
#target_link_libraries(tesseractwrap PRIVATE
#    pvt.cppan.demo.google.tesseract.libtesseract
#    pvt.cppan.demo.danbloomberg.leptonica
#)
#
#install(TARGETS
#            tesseractwrap
#        RUNTIME DESTINATION ocr
#        LIBRARY DESTINATION ocr
#        )