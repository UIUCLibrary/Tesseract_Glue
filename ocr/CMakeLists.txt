cppan_add_package(
    pvt.cppan.demo.google.tesseract.libtesseract
    pvt.cppan.demo.danbloomberg.leptonica
)
cppan_execute()
Python3_add_library(tesseractwrap MODULE hello.cpp)

target_link_libraries(tesseractwrap PRIVATE
    pvt.cppan.demo.google.tesseract.libtesseract
    pvt.cppan.demo.danbloomberg.leptonica
)

install(TARGETS
            tesseractwrap
        RUNTIME DESTINATION ocr
        LIBRARY DESTINATION ocr
        )