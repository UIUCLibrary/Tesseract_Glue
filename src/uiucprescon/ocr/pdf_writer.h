//
// Created by Borchers, Henry Samuel on 7/14/26.
//

#ifndef OCR_PDF_WRITER_H
#define OCR_PDF_WRITER_H
#include <functional>
#include <string>
#include <vector>

#include <tesseract/baseapi.h>

#include "Image.h"
#include "OCRApi.h"

enum class PDFWriteErrorCodes {
    Success,
    InitializationError,
    WriteError,
    ReadError,
    ProcessingError,
    NoPagesGiven,
    NoPDFWriter,
    UnknownError,
};

struct Pix;

namespace tesseract {
    class TESS_API TessBaseAPI;
    class TESS_API TessResultRenderer;
    class TESS_API TessPDFRenderer;
}  // namespace tesseract

using StartDocumentCallback = std::function<bool(const char*)>;
using EndDocumentCallback = std::function<bool()>;

class AbstractPDFWriteStrategy {
public:
    virtual PDFWriteErrorCodes generatePDF(const std::string &output_filename, const std::vector<std::string> &files, std::shared_ptr<OCRApi> api, const std::string &title) = 0;
    virtual ~AbstractPDFWriteStrategy() = default;
    virtual bool ProcessPage(const OCRApi &api, Pix *pix, int page_index, const char *filename, const char *retry_config, int timeout_millisec, tesseract::TessResultRenderer *renderer) = 0;
};

class TesseractPDFWriteStrategy: public AbstractPDFWriteStrategy {

public:
    virtual std::unique_ptr<tesseract::TessPDFRenderer> makeRenderer(const std::string& output_filename, const char *dataPath);

    bool ProcessPage(const OCRApi &api, Pix *pix, int page_index, const char *filename,
                     const char *retry_config, int timeout_millisec,
                     tesseract::TessResultRenderer *renderer) override;
    virtual PDFWriteErrorCodes BeginDocument(const std::string &title, const StartDocumentCallback &callback);
    virtual PDFWriteErrorCodes EndDocument(const EndDocumentCallback &callback);
    virtual std::shared_ptr<Image> loadImage(const std::string &filename);
    PDFWriteErrorCodes generatePDF(const std::string& output_filename, const std::vector<std::string> &files, std::shared_ptr<OCRApi> api);
    PDFWriteErrorCodes generatePDF(const std::string& output_filename, const std::vector<std::string> &files, std::shared_ptr<OCRApi> api, const std::string &title) override;
};

class IPDFWriter {
    public:
    PDFWriteErrorCodes write(const std::string &filename, const std::string &title="") const {
        return do_write(filename, title);
    };
    virtual void add_page(const std::string &filename) = 0;
    virtual ~IPDFWriter() = default;

private:
    virtual PDFWriteErrorCodes do_write(const std::string &filename, const std::string &title) const = 0;
};

class PDFWriter: public IPDFWriter {
    std::shared_ptr<AbstractPDFWriteStrategy> pdf_writer;
    std::vector<std::string> images;
    std::shared_ptr<OCRApi> m_api;

public:
    explicit PDFWriter(std::shared_ptr<OCRApi> api, const std::shared_ptr<AbstractPDFWriteStrategy> &writeStrategy=nullptr);
    PDFWriter(std::shared_ptr<OCRApi> api, const std::vector<std::string> &pages, const std::shared_ptr<AbstractPDFWriteStrategy> &writeStrategy=nullptr);
    size_t size() const;
    void add_page(const std::string &filename) override;

private:
    PDFWriteErrorCodes do_write(const std::string &filename, const std::string &title) const override;
};

#endif //OCR_PDF_WRITER_H
