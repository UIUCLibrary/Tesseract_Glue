add_library(glue OBJECT glue.cpp reader.cpp reader2.cpp utils.cpp fileLoader.cpp fileLoader.h ImageLoaderStrategies.cpp)
target_include_directories(glue PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(glue PUBLIC
        Tesseract::Tesseract
        )

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

install(CODE [[
    include(BundleUtilities)
    get_filename_component(deps_path "${CMAKE_SOURCE_DIR}/../../bin" ABSOLUTE)
    
    message(WARNING "USING ${deps_path} to find deps")
    find_program(TESSERACT 
        NAMES
            tesseract
        PATHS
            "${deps_path}"
    )

    file(COPY ${TESSERACT}
        DESTINATION ${CMAKE_INSTALL_PREFIX}/uiucprescon/ocr/tesseract/bin/
    )

    find_program(TESSERACT_INSTALLED 
        NAMES
            tesseract
        PATHS
            "${CMAKE_INSTALL_PREFIX}/uiucprescon/ocr/tesseract/bin/"
    )

    fixup_bundle(
        "${TESSERACT_INSTALLED}"
        ""
        "${deps_path}"
    )
]])