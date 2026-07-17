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

class IPDFBuilder {
public:
    virtual ~IPDFBuilder() = default;
    virtual PDFBuilderStatusCodes add_page(const std::string &file_path) = 0;
    virtual PDFBuilderStatusCodes open() = 0;
};

class PDFBuilder: public IPDFBuilder {
    std::string m_pdf_file_path;
    std::shared_ptr<OCRApi> m_api;
    std::string m_title;
    int m_page_index = -1;
    std::unique_ptr<tesseract::TessPDFRenderer>m_renderer;

public:
        explicit PDFBuilder(
            const std::string &file_path,
            const std::shared_ptr<OCRApi> &api,
            const std::string &title=std::string("")
        );
        PDFBuilderStatusCodes open() override;
        PDFBuilderStatusCodes add_page(const std::string &file_path) override;
        void close();
};


#endif //OCR_PDFBUILDER_H
