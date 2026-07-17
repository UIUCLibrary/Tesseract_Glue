//
// Created by Borchers, Henry Samuel on 7/17/26.
//

#include <filesystem>
#include <format>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>

#include <catch2/catch_test_macros.hpp>
#ifdef TEST_WITH_POPPLER
#include <poppler/cpp/poppler-document.h>
#endif

#include "OCRApi.h"
#include "PDFBuilder.h"

constexpr int MAX_TEMP_DIRS = 10;

namespace fs = std::filesystem;
namespace {

    class TempDirectory {
        fs::path m_path;
    public:
        TempDirectory() {

            for (int i=0; i<MAX_TEMP_DIRS; i++) {
                if (MAX_TEMP_DIRS-1 == i) {
                    throw std::runtime_error(std::format("Maximum number of temporary directories exceeded. Check {}", m_path.c_str()));
                }
                const std::string pattern = "test_dir_" + std::to_string(i);
                m_path = fs::temp_directory_path() /"tesseractglue"/ pattern;
                if (!fs::exists(m_path)) {
                    break;
                }
            }
            fs::create_directories(m_path);
        }

            ~TempDirectory() {
                fs::remove_all(m_path);
            }

        TempDirectory& operator=(TempDirectory other) {
            std::swap(m_path, other.m_path);
            return *this;
        }

        TempDirectory& operator=(TempDirectory &&other) noexcept {
            if (this != &other) {
                std::swap(m_path, other.m_path);
            }
            return *this;
        }

        TempDirectory(TempDirectory &&other) noexcept
            : m_path(std::move(other.m_path)) {}

        TempDirectory(const TempDirectory &other) : m_path(other.m_path) {};
        fs::path path() const{
            return m_path;
        }
    };
} // namespace

SCENARIO("PDF Builder") {
    GIVEN("PDFBuilder builder") {
        const TempDirectory dir;
        const auto output_pdf = std::string(dir.path() /"output.pdf");
        if (fs::exists(output_pdf)) {
            fs::remove(output_pdf);
        }
        const auto api = OCRApi::create(TESS_DATA, "eng");
        PDFBuilder builder(output_pdf, api);
        THEN("No pdf has generated yet") {
            REQUIRE(!fs::exists(output_pdf));
        }
        WHEN("PDFBuilder is opened") {
            builder.open();
            AND_WHEN("the document is closed") {
                builder.close();
                THEN("PDF has generated") {
                    REQUIRE(fs::exists(output_pdf));
                }
                THEN("PDF has zero pages") {
#ifdef TEST_WITH_POPPLER
                    builder.close();
                    const auto doc = std::shared_ptr<poppler::document>(poppler::document::load_from_file(output_pdf));
                    REQUIRE(doc);
                    REQUIRE(doc->pages() == 0);
#else
                    SKIP("Skipping: test requires poppler.");
#endif
                }
            }
            AND_WHEN("a invalid page is attempted to be added") {
                const auto return_status = builder.add_page("invalidfile.tif");
                THEN("the return status code is FileNotFound") {
                    REQUIRE(return_status == PDFBuilderStatusCodes::FileNotFound);
                }
            }
            AND_WHEN("a valid page is added") {
                const auto return_status = builder.add_page(TEST_IMAGE_PATH"/engwithheadings.tif");
                THEN("the return status code is success") {
                    REQUIRE(return_status == PDFBuilderStatusCodes::Success);
                }
                AND_WHEN("the document is closed") {
                    builder.close();
                    THEN("PDF has generated") {
                        REQUIRE(fs::exists(output_pdf));
                    }
                    THEN("PDF has 1 page") {
#ifdef TEST_WITH_POPPLER
                        const auto doc = std::unique_ptr<poppler::document>(poppler::document::load_from_file(output_pdf));
                        REQUIRE(doc);
                        REQUIRE(doc->pages() == 1);
#else
                        SKIP("Skipping: test requires poppler.");
#endif
                    }
                }
            }
        }
        if (fs::exists(output_pdf)) {
           fs::remove(output_pdf);
        }
    }

}
