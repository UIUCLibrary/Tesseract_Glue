#include "Image.h"
#include "fileLoader.h"
#include "glue.h"

#include "leptonica/allheaders.h"

#include <memory>
#include <string>
#include <vector>

#include "PDFBuilder.h"
#include "glueExceptions.h"

using std::string;
using std::shared_ptr;


namespace {
    void react_to_pdf_builder_add_pages(PDFBuilderStatusCodes return_code );
} //namespace


shared_ptr<Image> load_image(const string &source) {
    try {
        return ImageLoader::loadImage(source);

            } catch(const TesseractGlueException &e) {
                throw TesseractGlueException(e.what());
            }
        }

void pdf_builder_open(IPDFBuilder &self) {
    switch (self.open()) {
        case PDFBuilderStatusCodes::Success:
            return;
        case PDFBuilderStatusCodes::InitializationError:
            throw TesseractGlueException("Initialization Error");
        default:
            throw TesseractGlueException("Unknown error");
    }
}

void pdf_builder_add_pages(IPDFBuilder &self, const Image& image, const std::string &source) {
    react_to_pdf_builder_add_pages(self.add_page(image, source));
}
void pdf_builder_add_pages(IPDFBuilder &self, const std::string &file_path) {
    react_to_pdf_builder_add_pages(self.add_page(file_path));
}

namespace {
    void react_to_pdf_builder_add_pages(const PDFBuilderStatusCodes return_code ) {
        using enum PDFBuilderStatusCodes;
        switch (return_code) {
            case Success:
                return;
            case InitializationError:
                throw TesseractGlueException("Initialization Error");
            case FileNotFound:
                throw TesseractGlueException("File Not Found");
            case ReadError:
                throw TesseractGlueException("File Read Error");
            case ProcessingError:
                throw TesseractGlueException("Processing Error");
            default:
                throw TesseractGlueException("Unknown Error");
        }
    }
} // namespace
