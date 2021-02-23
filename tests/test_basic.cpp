#include "catch2/catch.hpp"
#include "glue.h"
#include "reader.h"
#include "reader2.h"
#include "glueExceptions.h"
#include <iostream>


TEST_CASE("dummy"){
    Reader2 reader(TESS_DATA, "eng");
    std::string d = reader.get_ocr(TEST_IMAGE_PATH "/" "engwithheadings.tif");
    std::cout  << d << std::endl;
    REQUIRE(!d.empty());
}

TEST_CASE("dummy2 blank page"){
    Reader2 reader(TESS_DATA, "eng");
//    std::string d = reader2.get_ocr(TEST_IMAGE);
    std::string d = reader.get_ocr(TEST_IMAGE_PATH "/" "blankpage.tif");
    std::cout  << d << std::endl;
    REQUIRE(!d.empty());
}

TEST_CASE("Reader2"){
    Reader2 reader(TESS_DATA, "eng");
    SECTION("invalid file throws an exception"){
        REQUIRE_THROWS_AS(reader.get_ocr("invalid_file.tif"), TesseractGlueException);
    }
}