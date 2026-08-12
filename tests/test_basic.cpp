#include "ImageLoaderStrategies.h"
#include "OCRApi.h"
#include "exceptions.h"
#include "fileLoader.h"
#include "reader2.h"

#include <catch2/catch_test_macros.hpp>

#include <iostream>
#include <memory>
#include <string>
#include <tuple>
#include <vector>

struct Pix;

namespace ocr = uiucprescon::ocr;
namespace {
    struct APIResource {
        APIResource() = default;
        std::shared_ptr<ocr::OCRApi> api = ocr::OCRApi::create(TESS_DATA, "eng");
    };
} // namespace

TEST_CASE_METHOD(APIResource, "dummy", "[slow]") {
    const ocr::Reader2 reader(api);
    std::string const data = reader.get_ocr(TEST_IMAGE_PATH "/engwithheadings.tif");
    std::cout << data << std::endl;
    REQUIRE(!data.empty());
}
TEST_CASE_PERSISTENT_FIXTURE(APIResource, "Reader2") {
    SECTION("get_ocr") {
        const ocr::Reader2 reader(api);

        SECTION("dummy2 blank page") {
            std::string const data = reader.get_ocr(TEST_IMAGE_PATH "/blankpage.tif");
            REQUIRE(data.empty());
        }
        SECTION("invalid file throws an exception") {
            REQUIRE_THROWS_AS(reader.get_ocr("invalid_file.tif"), ocr::OCRException);
        }
    }
}

TEST_CASE("Image") {
    GIVEN("An Empty Image") {
        const std::shared_ptr<Pix> data;
        const ocr::Image image(data);
        WHEN("Dimensions are checked") {
            THEN("Empty image has 0 for h") { REQUIRE(image.get_h() == 0); }
            THEN("Empty image has 0 for w") { REQUIRE(image.get_w() == 0); }
        }
    }
    GIVEN("An Image") {
        const ocr::Image image = *ocr::ImageLoader::loadImage(TEST_IMAGE_PATH "/engwithheadings.tif");
        WHEN("I make a copy with copy constructor") {
            const ocr::Image copy = image;
            THEN("The data is copied and has a new memory address") {
                REQUIRE(copy.getPix().get() != image.getPix().get());
            }
        }
        WHEN("I make a copy with copy assignment operator") {
            auto other = ocr::Image(std::shared_ptr<Pix>());
            other = image;
            THEN("The data is copied and has a new memory address") {
                REQUIRE(other.getPix().get() != image.getPix().get());
            }
        }
    }
}

TEST_CASE("Image size") {
    const std::vector<std::tuple<std::string, int, int>> test_cases = {
        {"blankpage.tif", 3000, 2234}, {"engwithheadings.tif", 3000, 1969}, {"engwithpicture.tif", 3000, 1982},
        {"ita.tif", 3000, 1826},       {"productionnotes.tif", 3000, 2065},
    };
    for (const auto& tuple : test_cases) {
        DYNAMIC_SECTION("checking " << std::get<0>(tuple)) {
            const std::string image_path = TEST_IMAGE_PATH;
            const std::shared_ptr<ocr::Image> image =
                ocr::ImageLoader::loadImage(image_path + "/" + std::get<0>(tuple));
            const auto height = std::get<1>(tuple);
            DYNAMIC_SECTION("image has height of " << height) { REQUIRE(image->get_h() == height); }
            const auto width = std::get<2>(tuple);
            DYNAMIC_SECTION("image has width of " << width) { REQUIRE(image->get_w() == width); }
        }
    }
}

TEST_CASE("ImageLoader") {
    SECTION("Load a dummyStrategy") {
        class dummyStrategy : public ocr::abcImageLoaderStrategy {
        public:
            std::shared_ptr<ocr::Image> load(const std::string& /*filename*/) override {
                return std::shared_ptr<ocr::Image>();
            }
        };
        dummyStrategy strategy;
        const std::shared_ptr<ocr::Image> my_image = ocr::ImageLoader::loadImage("invalid_file", strategy);
    }
}
