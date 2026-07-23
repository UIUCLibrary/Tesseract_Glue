#include "ImageLoaderStrategies.h"
#include "OCRApi.h"
#include "fileLoader.h"
#include "glue.h"
#include "glueExceptions.h"
#include "reader2.h"

#include <catch2/catch_test_macros.hpp>

#include <iostream>
#include <memory>
#include <string>
#include <tuple>
#include <vector>

struct Pix;

TEST_CASE("dummy"){
    const auto api = OCRApi::create(TESS_DATA, "eng");
    const Reader2 reader(api);
    std::string const data = reader.get_ocr(TEST_IMAGE_PATH "/" "engwithheadings.tif");
    std::cout  << data << std::endl;
    REQUIRE(!data.empty());
}

TEST_CASE("dummy2 blank page"){
    const auto api = OCRApi::create(TESS_DATA, "eng");
    const Reader2 reader(api);
    std::string const data = reader.get_ocr(TEST_IMAGE_PATH "/" "blankpage.tif");
    REQUIRE(data.empty());
}

TEST_CASE("Reader2"){
    SECTION("Valid reader"){
        auto api = OCRApi::create(TESS_DATA, "eng");
        const Reader2 reader(api);
        SECTION("invalid file throws an exception"){
            REQUIRE_THROWS_AS(reader.get_ocr("invalid_file.tif"), TesseractGlueException);
        }
    }
    // GIVEN("inValid reader"){
    //     const auto api = std::make_shared<OCRApi>("nodata", "spam");
    //     Reader2 reader(api);
    //     WHEN("reader is checked"){
    //         THEN("reader is not good"){
    //             REQUIRE(reader.isGood() == false);
    //         }
    //         THEN("get_ocr_from_image returns empty string"){
    //             std::shared_ptr<Image> i = load_image(TEST_IMAGE_PATH "/" "blankpage.tif");
    //             REQUIRE(reader.get_ocr_from_image(i).empty());
    //         }
    //     }
    // }
}

TEST_CASE("Image"){
    GIVEN("An Empty Image"){
        const std::shared_ptr<Pix> data;
        const Image image(data);
        WHEN("Dimensions are checked"){
            THEN("Empty image has 0 for h"){
                REQUIRE(image.get_h() == 0);
            }
            THEN("Empty image has 0 for w"){
                REQUIRE(image.get_w() == 0);
            }
        }

    }
}

TEST_CASE("Image size"){
    const std::vector<std::tuple<std::string, int, int>> test_cases = {
        {"blankpage.tif",       3000,   2234    },
        {"engwithheadings.tif", 3000,   1969    },
        {"engwithpicture.tif",  3000,   1982    },
        {"ita.tif",             3000,   1826    },
        {"productionnotes.tif", 3000,   2065    },
    };
    for (const auto& tuple : test_cases) {
        DYNAMIC_SECTION("checking " << std::get<0>(tuple)) {
            const std::string image_path = TEST_IMAGE_PATH;

            const std::shared_ptr<Image> image = load_image(image_path + "/" + std::get<0>(tuple));
            const auto height = std::get<1>(tuple);
            DYNAMIC_SECTION("image has height of " << height){
                REQUIRE(image->get_h() == height);
            }
            const auto width = std::get<2>(tuple);
            DYNAMIC_SECTION("image has width of " << width){
                REQUIRE(image->get_w() == width);
            }
        }
    }
}

TEST_CASE("ImageLoader"){
    SECTION("Load a dummyStrategy"){
        class dummyStrategy: public abcImageLoaderStrategy{
        public:
            std::shared_ptr<Image> load(const std::string& /*filename*/) override {
                return std::shared_ptr<Image>();
            }
        };

        dummyStrategy strategy;
        const std::shared_ptr<Image> my_image = ImageLoader::loadImage("invalid_file", strategy);
    }

}