#cppan_add_package(
#    pvt.cppan.demo.google.tesseract.libtesseract
#)
#cppan_execute()

add_library(glue OBJECT glue.cpp reader.cpp reader2.cpp utils.cpp)
target_include_directories(glue PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
#
target_link_libraries(glue PUBLIC
        libtesseract
        libleptonica
        )

#    pvt.cppan.demo.google.tesseract.libtesseract
##    pvt.cppan.demo.danbloomberg.leptonica
#)


#Python3_add_library(tesseractwrap MODULE tesseractwrap.cpp)
PYTHON_ADD_MODULE(tesseractwrap tesseractwrap.cpp)
if(PYTHON_EXTENSION_OUTPUT)
    message(STATUS "Changin to ${PYTHON_EXTENSION_OUTPUT}")
    set_target_properties(tesseractwrap PROPERTIES
        LIBRARY_OUTPUT_NAME ${PYTHON_EXTENSION_OUTPUT}
        RUNTIME_OUTPUT_NAME ${PYTHON_EXTENSION_OUTPUT}
    )
endif(PYTHON_EXTENSION_OUTPUT)

target_link_libraries(tesseractwrap
    PRIVATE
        glue
        pybind11::module
    )

install(TARGETS
            tesseractwrap
        RUNTIME DESTINATION uiucprescon/ocr
        LIBRARY DESTINATION uiucprescon/ocr
        )