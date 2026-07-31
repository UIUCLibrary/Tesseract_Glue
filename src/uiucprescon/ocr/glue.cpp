#include "Image.h"
#include "fileLoader.h"
#include "glue.h"

#include <memory>
#include <string>
#include <vector>

#include "PDFBuilder.h"
#include "glueExceptions.h"

using std::string;
using std::shared_ptr;

shared_ptr<Image> load_image(const string &source) {
    return ImageLoader::loadImage(source);
}

void pdf_builder_open(IPDFBuilder &self) {
    switch (self.open()) {
        case PDFBuilderStatusCodes::Success:
            return;
        case PDFBuilderStatusCodes::InitializationError:
            throw TesseractGlueException("Initialization Error");
        default:
            throw TesseractGlueException("Unknown error");
    };
}
void pdf_builder_add_pages(IPDFBuilder &self, const std::string &file_path) {
    using enum PDFBuilderStatusCodes;
    switch (self.add_page(file_path)) {
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