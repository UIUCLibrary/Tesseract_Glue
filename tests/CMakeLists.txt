set(TEST_FILES_BASE_URL "https://nexus.library.illinois.edu/repository/sample-data/ocr_test_images")

list(APPEND test_image_files blankpage.tif)
list(APPEND test_image_files engwithheadings.tif)
list(APPEND test_image_files engwithpicture.tif)
list(APPEND test_image_files ita.tif)
list(APPEND test_image_files productionnotes.tif)


if(BUILD_TESTING AND Catch2_FOUND)
    include(Catch)
    file(DOWNLOAD https://github.com/tesseract-ocr/tessdata/raw/4.0.0/eng.traineddata ${CMAKE_CURRENT_BINARY_DIR}/tessdata/eng.traineddata)
    file(DOWNLOAD https://github.com/tesseract-ocr/tessdata/raw/4.0.0/osd.traineddata ${CMAKE_CURRENT_BINARY_DIR}/tessdata/osd.traineddata)
    file(DOWNLOAD https://github.com/tesseract-ocr/tessconfigs/raw/3decf1c8252ba6dbeef0bf908f4b0aab7f18d113/pdf.ttf ${CMAKE_CURRENT_BINARY_DIR}/tessdata/pdf.ttf)

    foreach(image_file ${test_image_files})
        if(NOT EXISTS "${CMAKE_BINARY_DIR}/ocr_test_images/${image_file}")
            file(DOWNLOAD "${TEST_FILES_BASE_URL}/${image_file}" "${CMAKE_BINARY_DIR}/ocr_test_images/${image_file}")
        endif()
    endforeach()

    add_executable(tester
        test_basic.cpp
        test_pdf_writer.cpp
        test_PDFBuilder.cpp
        test_glue.cpp
        test_OCRApi.cpp
    )
    if (poppler_FOUND)
        target_compile_definitions(tester PRIVATE
            TEST_WITH_POPPLER
        )
        target_link_libraries(tester PRIVATE Catch2::Catch2WithMain poppler::poppler glue)
    endif ()
    target_compile_definitions(tester PRIVATE
        -DTESS_DATA="${CMAKE_CURRENT_BINARY_DIR}/tessdata"
        -DTEST_IMAGE_PATH="${CMAKE_BINARY_DIR}/ocr_test_images"
    )
    list(APPEND CMAKE_MODULE_PATH ${catch_SOURCE_DIR}/contrib/)
    catch_discover_tests(tester)
#    add_test(NAME test_basic COMMAND tester)
endif()