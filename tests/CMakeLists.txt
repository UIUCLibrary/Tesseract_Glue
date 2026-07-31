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
    file(READ ${CMAKE_CURRENT_SOURCE_DIR}/samplefiles.csv csv_data)
    string(REPLACE "\n" ";" csv_lines "${csv_data}")
    foreach(line IN LISTS csv_lines)
        # Skip empty lines
        if(line STREQUAL "")
            continue()
        endif()

        # Replace commas with semicolons to turn the line into a list
        string(REPLACE "," ";" columns "${line}")

        # Extract columns or do work
        list(POP_FRONT columns sample_file_name)
        string(STRIP "${sample_file_name}" sample_file_name)

        list(POP_FRONT columns sample_url)
        string(STRIP "${sample_url}" sample_url)

        list(POP_FRONT columns expected_sample_sha256_hash)
        string(STRIP "${expected_sample_sha256_hash}" expected_sample_sha256_hash)

        if(NOT EXISTS "${CMAKE_BINARY_DIR}/ocr_test_images/${sample_file_name}")
            file(DOWNLOAD "${sample_url}" "${CMAKE_BINARY_DIR}/ocr_test_images/${sample_file_name}" EXPECTED_HASH "SHA256=${expected_sample_sha256_hash}")
        else ()
            file(SHA256 "${CMAKE_BINARY_DIR}/ocr_test_images/${sample_file_name}" EXISTING_SAMPLE_FILE_HASH)
            if(NOT "${EXISTING_SAMPLE_FILE_HASH}" STREQUAL "${expected_sample_sha256_hash}")
                message(FATAL_ERROR "Integrity check failed! Hash mismatch for ${sample_file_name}. Expected: ${expected_sample_sha256_hash}. Got ${EXISTING_SAMPLE_FILE_HASH}")
            endif()
        endif ()
    endforeach()

    add_executable(tester
        test_basic.cpp
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