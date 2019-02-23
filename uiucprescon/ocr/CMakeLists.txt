add_library(glue OBJECT glue.cpp reader.cpp reader2.cpp utils.cpp)
target_include_directories(glue PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(glue PUBLIC
        leptonica
        ${Tesseract_LIBRARIES}
        )
target_include_directories(glue PUBLIC ${Tesseract_INCLUDE_DIRS} PRIVATE ${Leptonica_INCLUDE_DIRS})

add_library(tesseractwrap MODULE tesseractwrap.cpp)
    set_target_properties(tesseractwrap PROPERTIES
            PREFIX "${PYTHON_MODULE_PREFIX}"
            SUFFIX "${PYTHON_MODULE_EXTENSION}"
    )
#endif(PYTHON_EXTENSION_OUTPUT)

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