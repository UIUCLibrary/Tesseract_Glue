//
// Created by Borchers, Henry Samuel on 7/22/26.
//
#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>
#include <catch2/matchers/catch_matchers.hpp>
#include <catch2/matchers/catch_matchers_exception.hpp>

#include "Image.h"
#include "PDFBuilder.h"
#include "exceptions.h"
#include "glue.h"

#include <string>
#include <tuple>

#include "fileLoader.h"


using Catch::Matchers::Message;
namespace glue = uiucprescon::glue;
namespace ocr = uiucprescon::ocr;

SCENARIO("PDFBuilder") {
    class MockPDFBuilder : public ocr::IPDFBuilder {
    protected:
        PDFBuilderStatusCodes do_add_page(const ocr::Image& /*file_path*/, const std::string& /*file_path*/) override {
            return return_code;
        }
        PDFBuilderStatusCodes do_add_page(const std::string& /*file_path*/) override { return return_code; }

    public:
        PDFBuilderStatusCodes return_code =
            PDFBuilderStatusCodes::Success; // NOLINT(*-non-private-member-variables-in-classes)
        PDFBuilderStatusCodes open() override { return return_code; }
    };
    GIVEN("A Mock PDFBuilder") {
        auto strategy = MockPDFBuilder();
        WHEN("The return code of add_page() is success") {
            strategy.return_code = PDFBuilderStatusCodes::Success;
            THEN("Then no exception should be raised when running add_page()") {
                glue::pdf_builder_add_pages(strategy, "page.tif");
            }
        }
        WHEN("add_page() is run") {
            auto [enum_name, return_code, expected] = GENERATE(
                std::make_tuple("InitializationError", PDFBuilderStatusCodes::InitializationError,
                                "Initialization Error"),
                std::make_tuple("FileNotFound", PDFBuilderStatusCodes::FileNotFound, "File Not Found"),
                std::make_tuple("ReadError", PDFBuilderStatusCodes::ReadError, "File Read Error"),
                std::make_tuple("ProcessingError", PDFBuilderStatusCodes::ProcessingError, "Processing Error"));
            AND_WHEN("the return code is a " << enum_name) {
                strategy.return_code = return_code;
                THEN("Then the exception should be raised") {
                    REQUIRE_THROWS_MATCHES(glue::pdf_builder_add_pages(strategy, "page.tif"),
                                           glue::TesseractGlueException, Message(expected));
                }
            }
        }
        WHEN("open() is run") {
            AND_WHEN("The return code of open() is success") {
                strategy.return_code = PDFBuilderStatusCodes::Success;
                THEN("Then no exception should be raised") { glue::pdf_builder_open(strategy); }
            }
            auto [enum_name, return_code, expected] = GENERATE(std::make_tuple(
                "InitializationError", PDFBuilderStatusCodes::InitializationError, "Initialization Error"));
            AND_WHEN("open() is run and the return code is a " << enum_name) {
                strategy.return_code = return_code;
                THEN("Then the exception should be raised") {
                    REQUIRE_THROWS_MATCHES(glue::pdf_builder_open(strategy), glue::TesseractGlueException,
                                           Message(expected));
                }
            }
        }
    }
}
SCENARIO("react_pdf_builder_open_return_code") {
    GIVEN("A successfull return code from opening pdfbuilder") {
        const PDFBuilderStatusCodes return_code = PDFBuilderStatusCodes::Success;
        THEN("Then no exception should be raised") { glue::react_pdf_builder_open_return_code(return_code); }
    }
    GIVEN("a non success return code from opening pdfbuilder") {
        auto [enum_name, return_code, expected] = GENERATE(
            std::make_tuple("InitializationError", PDFBuilderStatusCodes::InitializationError, "Initialization Error"),
            std::make_tuple("ProcessingError", PDFBuilderStatusCodes::ProcessingError, "Unknown error"));
        WHEN("the return code is a " << enum_name) {
            THEN("Then the exception should be raised") {
                REQUIRE_THROWS_MATCHES(glue::react_pdf_builder_open_return_code(return_code),
                                       glue::TesseractGlueException, Message(expected));
            }
        }
    }
}

TEST_CASE("pixScaleToSize") {
    GIVEN("A valid image") {
        const auto image = ocr::ImageLoader::loadImage(TEST_IMAGE_PATH "/engwithheadings.tif");
        WHEN("I scale the image to a valid size") {
            const auto scaled_image = glue::pixScaleToSize(*image, 100, 100);
            THEN("The scaled image has the correct dimensions") {
                REQUIRE(scaled_image.get_w() == 100);
                REQUIRE(scaled_image.get_h() == 100);
            }
        }
        WHEN("I scale the image to an invalid size") {
            THEN("An exception is thrown for negative width") {
                REQUIRE_THROWS_AS(glue::pixScaleToSize(*image, -1, 100), glue::TesseractGlueException);
            }
            THEN("An exception is thrown for negative height") {
                REQUIRE_THROWS_AS(glue::pixScaleToSize(*image, 100, -1), glue::TesseractGlueException);
            }
            THEN("An exception is thrown for both width and height being zero") {
                REQUIRE_THROWS_AS(glue::pixScaleToSize(*image, 0, 0), glue::TesseractGlueException);
            }
        }
    }
}
