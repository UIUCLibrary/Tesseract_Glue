#include "glue.h"
#include "Image.h"
#include "fileLoader.h"

#include "leptonica/allheaders.h"

#include <memory>
#include <string>

#include "PDFBuilder.h"
#include "exceptions.h"

using std::shared_ptr;
using std::string;


namespace {
    void react_to_pdf_builder_add_pages(PDFBuilderStatusCodes return_code);
} // namespace


namespace uiucprescon::glue {
    shared_ptr<ocr::Image> load_image(const string& source) {
        try {
            return ocr::ImageLoader::loadImage(source);
        }
        catch (const ocr::OCRException& e) {
            throw TesseractGlueException(e.what());
        }
    }

    void pdf_builder_open(ocr::IPDFBuilder& self) {
        switch (self.open()) {
            case PDFBuilderStatusCodes::Success:
                return;
            case PDFBuilderStatusCodes::InitializationError:
                throw TesseractGlueException("Initialization Error");
            default:
                throw TesseractGlueException("Unknown error");
        }
    }

    ocr::Image pixScaleToSize(const ocr::Image& image, int targetWidth, int targetHeight) {
        if (targetWidth < 0 || targetHeight < 0) {
            throw TesseractGlueException("Invalid target image size. Value cannot be less than 0");
        }
        if (targetWidth == 0 && targetHeight == 0) {
            throw TesseractGlueException("Invalid target image size. Both target width and height cannot be 0.");
        }
        return ocr::Image(std::shared_ptr<Pix>(pixScaleToSize(image.getPix().get(), targetWidth, targetHeight),
                                               [](Pix* pix) { pixDestroy(&pix); }));
    }

    void pdf_builder_add_pages(ocr::IPDFBuilder& self, const ocr::Image& image, const std::string& source) {
        react_to_pdf_builder_add_pages(self.add_page(image, source));
    }

    void pdf_builder_add_pages(ocr::IPDFBuilder& self, const std::string& file_path) {
        react_to_pdf_builder_add_pages(self.add_page(file_path));
    }
} // namespace uiucprescon::glue

namespace {
    void react_to_pdf_builder_add_pages(const PDFBuilderStatusCodes return_code) {
        using enum PDFBuilderStatusCodes;
        namespace glue = uiucprescon::glue;

        switch (return_code) {
            case Success:
                return;
            case InitializationError:
                throw glue::TesseractGlueException("Initialization Error");
            case FileNotFound:
                throw glue::TesseractGlueException("File Not Found");
            case ReadError:
                throw glue::TesseractGlueException("File Read Error");
            case ProcessingError:
                throw glue::TesseractGlueException("Processing Error");
            default:
                throw glue::TesseractGlueException("Unknown Error");
        }
    }
} // namespace
