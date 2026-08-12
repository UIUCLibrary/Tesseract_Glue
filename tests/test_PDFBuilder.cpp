//
// Created by Borchers, Henry Samuel on 7/17/26.
//

#include <filesystem>
#include <format>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>

#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>

#ifdef TEST_WITH_POPPLER
#include <poppler/cpp/poppler-document.h>
#endif

#include "Image.h"
#include "OCRApi.h"
#include "PDFBuilder.h"
#include "exceptions.h"

constexpr int MAX_TEMP_DIRS = 10;

namespace fs = std::filesystem;
namespace ocr = uiucprescon::ocr;

namespace {

    class TempDirectory {
        fs::path m_path;

    public:
        TempDirectory() {

            for (int i = 0; i < MAX_TEMP_DIRS; i++) {
                if (MAX_TEMP_DIRS - 1 == i) {
                    throw std::runtime_error(
                        std::format("Maximum number of temporary directories exceeded. Check {}", m_path.c_str()));
                }
                const std::string pattern = "test_dir_" + std::to_string(i);
                m_path = fs::temp_directory_path() / "tesseractglue" / pattern;
                if (!fs::exists(m_path)) {
                    break;
                }
            }
            fs::create_directories(m_path);
        }

        ~TempDirectory() { fs::remove_all(m_path); }

        TempDirectory& operator=(TempDirectory other) {
            std::swap(m_path, other.m_path);
            return *this;
        }

        TempDirectory& operator=(TempDirectory&& other) noexcept {
            if (this != &other) {
                std::swap(m_path, other.m_path);
            }
            return *this;
        }

        TempDirectory(TempDirectory&& other) noexcept : m_path(std::move(other.m_path)) {}

        TempDirectory(const TempDirectory& other) : m_path(other.m_path) {};

        fs::path path() const { return m_path; }
    };

    struct APIResource {
        APIResource() = default;

        fs::path get_temp_dir() const { return dir.path(); }

    protected:
        std::shared_ptr<ocr::OCRApi> api = ocr::OCRApi::create(TESS_DATA, "eng");

    private:
        TempDirectory dir;
    };
} // namespace

TEST_CASE("renderer is ready") {
    SECTION("null ptr") { REQUIRE(ocr::is_renderer_ready_to_use(nullptr) == false); }
}
TEST_CASE_PERSISTENT_FIXTURE(APIResource, "PDF Builder") {
    class TestablePDFBuilder : public ocr::PDFBuilder {
    protected:
        bool renderer_is_ready() const noexcept final { return is_renderer_is_ready; }
        bool process_page(std::shared_ptr<Pix> /*pix*/, int /*page_index*/, const std::string& /*filename*/,
                          const char* /*retry_config*/, int /*timeout_millisec*/) const final {
            process_side_effect();
            return is_process_page_successful;
        }

    public:
        TestablePDFBuilder(std::string const& path, const std::shared_ptr<ocr::OCRApi>& api) : PDFBuilder(path, api) {}
        // NOLINTBEGIN(misc-non-private-member-variables-in-classes)
        std::function<void()> process_side_effect = []() { /*by default this is a noop*/ };
        bool is_renderer_is_ready = true;
        bool is_process_page_successful = true;
        // NOLINTEND(misc-non-private-member-variables-in-classes)
    };

    SECTION("PDFBuilder.create_renderer()") {
        auto const& file_name = GENERATE(as<std::string>{}, "output", "output.pdf");
        DYNAMIC_SECTION("Testing with file name: " << file_name) {
            TestablePDFBuilder builder(file_name, api);
            builder.is_renderer_is_ready = true;
            REQUIRE(builder.open() == PDFBuilderStatusCodes::Success);
        }
    }
    GIVEN("A testable pdf builder") {
        const auto output_pdf = std::string(get_temp_dir() / "output.pdf");
        TestablePDFBuilder builder(output_pdf, api);
        WHEN("renderer is not ready") {
            builder.is_renderer_is_ready = false;
            THEN("the return code for add_page is InitializationError") {
                REQUIRE(builder.add_page(ocr::Image(nullptr)) == PDFBuilderStatusCodes::InitializationError);
            }
            THEN("trying to open() will return a InitializationError status code") {
                REQUIRE(builder.open() == PDFBuilderStatusCodes::InitializationError);
            }
        }
        WHEN("renderer is ready") {
            builder.is_renderer_is_ready = true;
            AND_WHEN("process_page will not be successful") {
                builder.is_process_page_successful = false;
                THEN("the return code for add_page is ProcessingError") {
                    REQUIRE(builder.add_page(ocr::Image(nullptr)) == PDFBuilderStatusCodes::ProcessingError);
                }
            }
            AND_WHEN("process_page throws an OCRException") {
                builder.is_process_page_successful = false;
                builder.process_side_effect = []() { throw ocr::OCRException("test exception"); };
                THEN("the return code for add_page returns a read error") {
                    REQUIRE(builder.add_page(ocr::Image(nullptr)) == PDFBuilderStatusCodes::ReadError);
                }
            }
        }
    }
}

TEST_CASE_PERSISTENT_FIXTURE(APIResource, "PDF Builder success", "[slow]") {

    GIVEN("PDFBuilder builder") {
        const auto output_pdf = std::string(get_temp_dir() / "output.pdf");
        if (fs::exists(output_pdf)) {
            fs::remove(output_pdf);
        }
        ocr::PDFBuilder builder(output_pdf, api);
        THEN("No pdf has generated yet") { REQUIRE(!fs::exists(output_pdf)); }
        WHEN("PDFBuilder is opened") {
            builder.open();
            AND_WHEN("the document is closed") {
                builder.close();
                THEN("PDF has generated") { REQUIRE(fs::exists(output_pdf)); }
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
                const auto return_status = builder.add_page(TEST_IMAGE_PATH "/engwithheadings.tif");
                THEN("the return status code is success") {
                    REQUIRE(return_status == PDFBuilderStatusCodes::Success);
                    AND_WHEN("the document is closed") {
                        builder.close();
                        THEN("PDF has generated") {
                            REQUIRE(fs::exists(output_pdf));
                            AND_WHEN("PDF has 1 page") {
#ifdef TEST_WITH_POPPLER
                                const auto doc =
                                    std::unique_ptr<poppler::document>(poppler::document::load_from_file(output_pdf));
                                CHECK(doc);
                                CHECK(doc->pages() == 1);
#else
                                SKIP("Skipping: test requires poppler.");
#endif
                            }
                        }
                    }
                }
            }
        }
        if (fs::exists(output_pdf)) {
            fs::remove(output_pdf);
        }
    }
}
