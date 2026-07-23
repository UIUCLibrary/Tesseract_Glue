//
// Created by Borchers, Henry Samuel on 7/22/26.
//
#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>
#include <catch2/matchers/catch_matchers.hpp>
#include <catch2/matchers/catch_matchers_exception.hpp>

#include "PDFBuilder.h"
#include "glue.h"
#include "pdf_writer.h"

#include <memory>
#include <string>
#include <tuple>

#include "glueExceptions.h"

using Catch::Matchers::Message;

SCENARIO("PDFBuilder") {
    class MockPDFBuilder : public IPDFBuilder {
    public:
        PDFBuilderStatusCodes return_code = PDFBuilderStatusCodes::Success; // NOLINT(*-non-private-member-variables-in-classes)
        PDFBuilderStatusCodes add_page(const std::string& /*file_path*/) override {
            return return_code;
        }
        PDFBuilderStatusCodes open() override {
            return return_code;
        }
    };
    GIVEN("A Mock PDFBuilder") {
        auto strategy = MockPDFBuilder();
        WHEN("The return code of add_page() is success") {
            strategy.return_code = PDFBuilderStatusCodes::Success;
            THEN("Then no exception should be raised when running add_page()") {
                pdf_builder_add_pages(strategy, "page.tif");
            }
        }
        WHEN("add_page() is run") {
            auto [enum_name, return_code, expected] = GENERATE(
                std::make_tuple("InitializationError", PDFBuilderStatusCodes::InitializationError, "Initialization Error"),
                std::make_tuple("FileNotFound", PDFBuilderStatusCodes::FileNotFound, "File Not Found"),
                std::make_tuple("ReadError", PDFBuilderStatusCodes::ReadError, "File Read Error"),
                std::make_tuple("ProcessingError", PDFBuilderStatusCodes::ProcessingError, "Processing Error")
            );
            AND_WHEN("the return code is a " << enum_name) {
                strategy.return_code = return_code;
                THEN("Then the exception should be raised") {
                    REQUIRE_THROWS_MATCHES(pdf_builder_add_pages(strategy, "page.tif"),TesseractGlueException, Message(expected));
                }
            }
        }
        WHEN("open() is run") {
            AND_WHEN("The return code of open() is success") {
                strategy.return_code = PDFBuilderStatusCodes::Success;
                THEN("Then no exception should be raised") {
                    pdf_builder_open(strategy);
                }
            }
            auto [enum_name, return_code, expected] = GENERATE(
                std::make_tuple("InitializationError", PDFBuilderStatusCodes::InitializationError, "Initialization Error")
            );
            AND_WHEN("open() is run and the return code is a " << enum_name) {
                strategy.return_code = return_code;
                THEN("Then the exception should be raised") {
                    REQUIRE_THROWS_MATCHES(pdf_builder_open(strategy),TesseractGlueException, Message(expected));
                }
            }
        }
    }
}

SCENARIO("create_pdf") {
    struct MockStrategy: IPDFWriter {
        PDFWriteErrorCodes return_code = PDFWriteErrorCodes::Success; // NOLINT(*-non-private-member-variables-in-classes)
        int number_of_pages_added = 0; // NOLINT(*-non-private-member-variables-in-classes)
        void add_page(const std::string &/*filename*/) override {
            number_of_pages_added++;
        };
    private:
        PDFWriteErrorCodes do_write(const std::string& /*filename*/, const std::string& /*title*/) const override {
            return return_code;
        };
    };
    GIVEN("A mock strategy") {
        auto strategy = MockStrategy();
        WHEN("create_pdf() is run with without an api given") {
            THEN("Then an exception should be raised") {
                REQUIRE_THROWS_AS(create_pdf({""},"output.pdf", nullptr, &strategy), TesseractGlueException);
            }
        }
        AND_GIVEN("An Api object") {
            const auto api = OCRApi::create(TESS_DATA, "eng");

            WHEN("create_pdf() is run with a single page") {
                create_pdf({""},"output.pdf", api, &strategy);
                THEN("The add_page pages was called because number_of_pages_added was set to one") {
                    REQUIRE(strategy.number_of_pages_added == 1);
                }
            }
            auto [enum_name, return_code, expected] = GENERATE(
                std::make_tuple("InitializationError", PDFWriteErrorCodes::InitializationError, "Initialization Error"),
                std::make_tuple("ProcessingError", PDFWriteErrorCodes::ProcessingError, "Processing Error"),
                std::make_tuple("NoPagesGiven", PDFWriteErrorCodes::NoPagesGiven, "No Pages Given"),
                std::make_tuple("WriteError", PDFWriteErrorCodes::WriteError, "Write Error"),
                std::make_tuple("UnknownError", PDFWriteErrorCodes::UnknownError, "Unknown Error")
            );
            WHEN("create_pdf() is run and the return code is a " << enum_name) {
                strategy.return_code = return_code;
                THEN("Then the exception should be raised") {
                    REQUIRE_THROWS_MATCHES(create_pdf({""},"output.pdf", api, &strategy), TesseractGlueException, Message(expected));
                }
            }
        }
    }
}