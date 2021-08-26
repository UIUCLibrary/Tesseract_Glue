#include "catch2/catch.hpp"
#include "glue.h"
#include "reader.h"
#include "reader2.h"
#include "glueExceptions.h"
#include "fileLoader.h"
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
    SECTION("Valid reader"){
        Reader2 reader(TESS_DATA, "eng");
        SECTION("invalid file throws an exception"){
            REQUIRE_THROWS_AS(reader.get_ocr("invalid_file.tif"), TesseractGlueException);
        }
    }
    GIVEN("inValid reader"){
        Reader2 reader("nodata", "spam");
        WHEN("reader is checked"){
            THEN("reader is not good"){
                REQUIRE(reader.isGood() == false);
            }
            THEN("get_ocr_from_image returns empty string"){
                std::shared_ptr<Image> i = load_image(TEST_IMAGE_PATH "/" "blankpage.tif");
                REQUIRE(reader.get_ocr_from_image(i).empty());
            }
        }
    }
}

TEST_CASE("Image"){
    GIVEN("An Empty Image"){
        std::shared_ptr<Pix> d;
        Image s(d);
        WHEN("Dimensions are checked"){
            THEN("Empty image has 0 for h"){
                REQUIRE(s.get_h() == 0);
            }
            THEN("Empty image has 0 for w"){
                REQUIRE(s.get_w() == 0);
            }
        }

    }

}
TEST_CASE("ImageLoader"){
    SECTION("Load a dummyStrategy"){
        class dummyStrategy: public abcImageLoaderStrategy{
        public:
            std::shared_ptr<Image> load(const std::string &filename) override {
                return std::shared_ptr<Image>();
            }
        };

        dummyStrategy d;
        std::shared_ptr<Image> s = ImageLoader::loadImage("invalid_file", d);
    }

}