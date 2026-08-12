//
// Created by Borchers, Henry Samuel on 7/17/26.
//

#ifndef OCR_PDFBUILDER_H
#define OCR_PDFBUILDER_H

#include <memory>
#include <string>

#include <tesseract/renderer.h>

#include "OCRApi.h"

namespace tesseract {
    class TESS_API TessBaseAPI;
    class TESS_API TessPDFRenderer;
} // namespace tesseract


enum class PDFBuilderStatusCodes {
    Success,
    InitializationError,
    ReadError,
    ProcessingError,
    FileNotFound,
};
namespace uiucprescon::ocr {
    bool is_renderer_ready_to_use(const tesseract::TessPDFRenderer* renderer);
    class Image;

    class IPDFBuilder {
    protected:
        virtual PDFBuilderStatusCodes do_add_page(const Image& image, const std::string& file_path) = 0;
        virtual PDFBuilderStatusCodes do_add_page(const std::string& file_path) = 0;

    public:
        virtual ~IPDFBuilder() = default;

        PDFBuilderStatusCodes add_page(const Image& image, const std::string& file_path = "") {
            return do_add_page(image, file_path);
        };
        virtual PDFBuilderStatusCodes add_page(const std::string& file_path) { return do_add_page(file_path); }
        virtual PDFBuilderStatusCodes open() = 0;
    };

    class PDFBuilder : public IPDFBuilder {
        std::string m_pdf_file_path;
        std::shared_ptr<OCRApi> m_api;
        std::string m_title;
        int m_page_index = -1;
        std::unique_ptr<tesseract::TessPDFRenderer> m_renderer;

    protected:
        PDFBuilderStatusCodes do_add_page(const Image& image, const std::string& file_path) override;
        PDFBuilderStatusCodes do_add_page(const std::string& file_path) override;
        virtual bool renderer_is_ready() const noexcept;
        virtual bool process_page(std::shared_ptr<Pix> pix, int page_index, const std::string& filename,
                                  const char* retry_config, int timeout_millisec) const;
        virtual std::unique_ptr<tesseract::TessPDFRenderer> create_renderer() const noexcept;

    public:
        explicit PDFBuilder(const std::string& file_path, const std::shared_ptr<OCRApi>& api,
                            const std::string& title = std::string(""));
        PDFBuilderStatusCodes open() override;
        void close();
    };
} // namespace uiucprescon::ocr

#endif // OCR_PDFBUILDER_H
