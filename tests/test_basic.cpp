#include "catch2/catch.hpp"
#include "glue.h"
#include "reader.h"
#include <iostream>


TEST_CASE("dummy"){
    Reader reader(TESS_DATA, "eng");
    std::string d = reader.get_ocr(TEST_IMAGE);
    std::cout  << d << std::endl;
    REQUIRE(!d.empty());
}