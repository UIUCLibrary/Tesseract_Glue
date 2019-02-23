if(BUILD_TESTING)
    include(FetchContent)
    FetchContent_Declare(
        libcatch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG 15cf3ca
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
#    file(DOWNLOAD https://github.com/tesseract-ocr/tessdata/raw/4.00/eng.traineddata ${CMAKE_CURRENT_BINARY_DIR}/tessdata/eng.traineddata)
#    file(DOWNLOAD https://jenkins.library.illinois.edu/userContent/IlliniLore_1944_00000011.tif ${CMAKE_CURRENT_BINARY_DIR}/IlliniLore_1944_00000011.tif)

    FetchContent_Declare(
        test_images
        URL        https://jenkins.library.illinois.edu/userContent/ocr_test_images.zip
    )

    FetchContent_GetProperties(test_images)
    if(NOT test_images_POPULATED)
        FetchContent_Populate(test_images)
    endif()



    target_include_directories(Catch2 INTERFACE ${libcatch2_SOURCE_DIR}/single_include)
    include(Catch)
    add_executable(tester test-main.cpp test_basic.cpp)
    target_link_libraries(tester PRIVATE Catch2 glue)
    target_compile_definitions(tester PRIVATE 
        -DTESS_DATA="${CMAKE_CURRENT_BINARY_DIR}/tessdata"
        -DTEST_IMAGE_PATH="${test_images_SOURCE_DIR}"
    )
    catch_discover_tests(tester)
#    add_test(NAME test_basic COMMAND tester)
endif()