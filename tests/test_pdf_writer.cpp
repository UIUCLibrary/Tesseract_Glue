//
// Created by Borchers, Henry Samuel on 7/14/26.
//
#include "fileLoader.h"
#include "Image.h"
#include "ImageLoaderStrategies.h"
#include "OCRApi.h"
#include "pdf_writer.h"
#include <catch2/catch_test_macros.hpp>

#include <leptonica/allheaders.h>
#include <leptonica/environ.h>
#include <tesseract/renderer.h>

#include <memory>
#include <string>
#include <vector>

namespace {
    struct MockPdfWriter: AbstractPDFWriteStrategy {
        // NOLINTNEXTLINE(bugprone-easily-swappable-parameters)
        bool ProcessPage(const OCRApi& /*api*/, Pix* /*pix*/, int /*page_index*/, const char* /*filename*/, const char* /*retry_config*/, int /*timeout_millisec*/, tesseract::TessResultRenderer* /*renderer*/) override {
            return true;
        }
        PDFWriteErrorCodes generatePDF(const std::string& /*output_filename*/, const std::vector<std::string>& /*output_filename*/, std::shared_ptr<OCRApi> /*api*/, const std::string & /*title*/) override{
            m_times_written++;
            return PDFWriteErrorCodes::Success;
        }
        int times_written() const{
            return m_times_written;
        }
    private:
        int m_times_written{0};
    };
} // namespace

SCENARIO("PDF Writer") {
    setMsgSeverity(L_SEVERITY_ALL);
    auto api = OCRApi::create(TESS_DATA, "eng");
    GIVEN("A Pdf Writer with a mock writer and a path to a fake file") {
        std::shared_ptr<MockPdfWriter> const mockPdfWriter = std::make_shared<MockPdfWriter>();
        const std::string sample_image = "somepath/IlliniLore_1944_00000011.tif";
        AND_GIVEN("A non-const Pdf Writer using the mock writer") {
            PDFWriter pdf_writer(api, mockPdfWriter);
            REQUIRE(pdf_writer.size() == 0);
            WHEN("adding a page") {
                pdf_writer.add_page(sample_image);
                THEN("This size of the object increases") {
                    REQUIRE(pdf_writer.size() == 1);
                }
                AND_WHEN("Write a .pdf file from image files") {
                    REQUIRE(mockPdfWriter->times_written() == 0);
                    auto return_code =pdf_writer.write("somepath/output.pdf");
                    THEN("The return code is a success") {
                        REQUIRE(return_code == PDFWriteErrorCodes::Success);
                    }
                    THEN("A new pdf file is written") {
                        REQUIRE(mockPdfWriter->times_written() == 1);
                    }
                }
            }
        }
        AND_GIVEN("A const Pdf Writer using the mock writer with no pages already declared") {
            const PDFWriter pdf_writer(api, mockPdfWriter);
            WHEN("Attempting to write a .pdf file") {
                auto return_code = pdf_writer.write("somepath/output.pdf");
                THEN("Return code is a no pages error") {
                    REQUIRE(return_code == PDFWriteErrorCodes::NoPagesGiven);
                }
                THEN("not new pdf file is written") {
                    REQUIRE(mockPdfWriter->times_written() == 0);
                }
            }
        }
        AND_GIVEN("A const Pdf Writer using the mock writer with at least one page already declared") {
            const PDFWriter pdf_writer(api, std::vector{sample_image}, mockPdfWriter);
            WHEN("Attempting to write a .pdf file") {
                auto return_code = pdf_writer.write("somepath/output.pdf");
                THEN("Return code is a no pages error") {
                    REQUIRE(return_code == PDFWriteErrorCodes::Success);
                }
                THEN("new pdf file is written") {
                    REQUIRE(mockPdfWriter->times_written() > 0);
                }
            }
        }
    }
}

TEST_CASE("TesseractPDFWriteStrategy") {
    const std::shared_ptr<OCRApi> api = OCRApi::create(TESS_DATA, "eng");
    SECTION("unsuccessful to close a document with EndDocument") {
        auto strategy = TesseractPDFWriteStrategy();
        const PDFWriteErrorCodes return_code = strategy.EndDocument([](){return false;});
        REQUIRE(return_code != PDFWriteErrorCodes::Success);
    }
    SECTION("successful to close a document with EndDocument") {
        auto strategy = TesseractPDFWriteStrategy();
        const PDFWriteErrorCodes return_code = strategy.EndDocument([](){return true;});
        REQUIRE(return_code == PDFWriteErrorCodes::Success);
    }
    SECTION("unsuccessful to open a document with BeginDocument") {
        auto strategy = TesseractPDFWriteStrategy();

        // NOLINTNEXTLINE(readability-identifier-length)
        const PDFWriteErrorCodes return_code = strategy.BeginDocument("somefile", [](const char* /*_*/){return false;});
        REQUIRE(return_code == PDFWriteErrorCodes::WriteError);
    }
    SECTION("successfully open a document with BeginDocument") {
        auto strategy = TesseractPDFWriteStrategy();

        // NOLINTNEXTLINE(readability-identifier-length)
        const PDFWriteErrorCodes return_code = strategy.BeginDocument("somefile", [](const char* /*_*/){return true;});
            REQUIRE(return_code == PDFWriteErrorCodes::Success);
    }
}

SCENARIO("TesseractPDFWriteStrategy") {
    struct MockLoadImageStrategy:abcImageLoaderStrategy{
        std::shared_ptr<Image> load(const std::string& /*filename*/) override{
            return m_image;
        }

        void set_image(std::shared_ptr<Image> image) {
            m_image = image;
        }
    private:
        std::shared_ptr<Image> m_image = nullptr;
    };
    struct MockTesseractPDFWriteStrategy : TesseractPDFWriteStrategy {
        std::unique_ptr<tesseract::TessPDFRenderer> makeRenderer(const std::string& /*output_filename*/, const char* /*dataPath*/) override{
            return std::unique_ptr<tesseract::TessPDFRenderer>();
        }

        void begin_document_return_code(const PDFWriteErrorCodes return_code) {
            m_begin_document_return_code = return_code;
        }
        PDFWriteErrorCodes BeginDocument(const std::string& /*title*/, const StartDocumentCallback& /*callback*/) override {
            return m_begin_document_return_code;
        };

        PDFWriteErrorCodes EndDocument(const EndDocumentCallback & /*callback*/) override {
            return m_end_document_return_code;
        };

        std::shared_ptr<Image> loadImage(const std::string &filename) override {
            auto strategy = MockLoadImageStrategy();
            strategy.set_image(m_returned_image);
            return ImageLoader::loadImage(filename, strategy);
        };
        void process_page_is_successful(bool is_successful) {
            m_process_page_is_successful = is_successful;
        }

        // NOLINTNEXTLINE(bugprone-easily-swappable-parameters)
        bool ProcessPage(const OCRApi& /*api*/, Pix* /*pix*/, int /*page_index*/, const char* /*filename*/, const char* /*retry_config*/, int /*timeout_millisec*/, tesseract::TessResultRenderer* /*renderer*/) override {
            process_page_called++;
            return m_process_page_is_successful;
        }
        int get_number_of_processed_pages() const {
            return process_page_called;
        }
        void returned_image(const std::shared_ptr<Image> &returned_image) {
            m_returned_image = returned_image;
        }
        void end_document_return_code(PDFWriteErrorCodes return_code) {
            m_end_document_return_code = return_code;
        }
    private:
        int process_page_called = 0;
        PDFWriteErrorCodes m_end_document_return_code = PDFWriteErrorCodes::Success;
        PDFWriteErrorCodes m_begin_document_return_code = PDFWriteErrorCodes::Success;
        bool m_process_page_is_successful = true;
        std::shared_ptr<Image> m_returned_image = std::make_shared<Image>(std::shared_ptr<Pix>(nullptr));
    };
    GIVEN("a TesseractPDFWriteStrategy object") {
        const auto api = OCRApi::create(TESS_DATA,"eng");
        MockTesseractPDFWriteStrategy strategy;

        WHEN("Attempting to write a .pdf file") {
            const PDFWriteErrorCodes return_code = strategy.generatePDF( "output.pdf", std::vector<std::string>{"samplefile.tif"}, api);
            THEN("the return code is successful") {
                REQUIRE(return_code == PDFWriteErrorCodes::Success);
            }
            THEN("I have processed at least one page") {
                REQUIRE(strategy.get_number_of_processed_pages() > 0);
            }
        }
        AND_GIVEN("input file is invalid") {
            strategy.returned_image(nullptr);
            WHEN("Attempting to write a .pdf file") {
                const PDFWriteErrorCodes return_code = strategy.generatePDF("output.pdf", std::vector<std::string>{"samplefile.tif"}, api);
                THEN("the return code is invalid") {
                    REQUIRE(return_code == PDFWriteErrorCodes::ReadError);
                }
            }
        }
        AND_GIVEN("input is valid but the file is unable to be processed") {
            strategy.returned_image(std::make_shared<Image>(std::shared_ptr<Pix>(nullptr)));
            strategy.process_page_is_successful(false);
            WHEN("Attempting to write a .pdf file") {
                const PDFWriteErrorCodes return_code = strategy.generatePDF("output.pdf", std::vector<std::string>{"samplefile.tif"}, api);
                THEN("the return code is a processing error") {
                    REQUIRE(return_code == PDFWriteErrorCodes::ProcessingError);
                }
            }
        }
        AND_GIVEN("output file and input file are valid but closing the file will cause an error") {
            strategy.returned_image(std::make_shared<Image>(std::shared_ptr<Pix>(nullptr)));
            strategy.process_page_is_successful(true);
            strategy.begin_document_return_code(PDFWriteErrorCodes::Success);
            strategy.end_document_return_code(PDFWriteErrorCodes::UnknownError);
            WHEN("Attempting to write a .pdf file") {
                const PDFWriteErrorCodes return_code = strategy.generatePDF("output.pdf", std::vector<std::string>{"samplefile.tif"}, api);
                THEN("the return code is not successful") {
                    REQUIRE(return_code != PDFWriteErrorCodes::Success);
                }
            }
        }
        AND_GIVEN("output file is invalid") {
            strategy.begin_document_return_code(PDFWriteErrorCodes::WriteError);
            WHEN("Attempting to write a .pdf file") {
                const PDFWriteErrorCodes return_code = strategy.generatePDF("output.pdf", std::vector<std::string>{"samplefile.tif"}, api);
                THEN("the return code is not successful") {
                    REQUIRE(return_code != PDFWriteErrorCodes::Success);
                }
                THEN("I have processed no pages") {
                    REQUIRE(strategy.get_number_of_processed_pages() == 0);
                }
            }
        }
    }
}
