set(TEST_FILES_BASE_URL "https://jenkins.library.illinois.edu/nexus/repository/sample-data/ocr_test_images")

list(APPEND test_image_files blankpage.tif)
list(APPEND test_image_files engwithheadings.tif)
list(APPEND test_image_files engwithpicture.tif)
list(APPEND test_image_files ita.tif)
list(APPEND test_image_files productionnotes.tif)


if(BUILD_TESTING)
    include(FetchContent)
    FetchContent_Declare(
        libcatch2
            URL https://github.com/catchorg/Catch2/archive/v2.13.4.tar.gz
#        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
#        GIT_TAG 15cf3ca
    )

    FetchContent_GetProperties(libcatch2)
    if(NOT libcatch2_POPULATED)
        FetchContent_Populate(libcatch2)
        add_library(Catch2 INTERFACE)
        list(APPEND CMAKE_MODULE_PATH ${libcatch2_SOURCE_DIR}/contrib/)
    endif()
#
    file(DOWNLOAD https://github.com/tesseract-ocr/tessdata/raw/4.0.0/eng.traineddata ${CMAKE_CURRENT_BINARY_DIR}/tessdata/eng.traineddata)
    file(DOWNLOAD https://github.com/tesseract-ocr/tessdata/raw/4.0.0/osd.traineddata ${CMAKE_CURRENT_BINARY_DIR}/tessdata/osd.traineddata)

    foreach(image_file ${test_image_files})
        if(NOT EXISTS "${CMAKE_BINARY_DIR}/ocr_test_images/${image_file}")
            file(DOWNLOAD "${TEST_FILES_BASE_URL}/${image_file}" "${CMAKE_BINARY_DIR}/ocr_test_images/${image_file}")
        endif()
    endforeach()



    target_include_directories(Catch2 INTERFACE ${libcatch2_SOURCE_DIR}/single_include)
    include(Catch)
    add_executable(tester test-main.cpp test_basic.cpp)
    target_link_libraries(tester PRIVATE Catch2 glue)
    target_compile_definitions(tester PRIVATE 
        -DTESS_DATA="${CMAKE_CURRENT_BINARY_DIR}/tessdata"
        -DTEST_IMAGE_PATH="${CMAKE_BINARY_DIR}/ocr_test_images"
    )
    catch_discover_tests(tester)
#    add_test(NAME test_basic COMMAND tester)
endif()