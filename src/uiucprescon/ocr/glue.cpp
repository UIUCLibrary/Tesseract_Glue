#include "Image.h"
#include "fileLoader.h"
#include "glue.h"

#include <memory>
#include <string>
#include <vector>

#include "PDFBuilder.h"
#include "glueExceptions.h"
#include "pdf_writer.h"

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

void create_pdf(const std::vector<std::string> &files, const std::string &output, const std::shared_ptr<OCRApi> &api, IPDFWriter *strategy) {
    using enum PDFWriteErrorCodes;
    if (!api) {
        throw TesseractGlueException("Invalid OCRApi");
    }

    // Use default pdf creation strategy if not provided with one
    IPDFWriter *activeStrategy = nullptr;
    std::unique_ptr<PDFWriter> defaultStrategy = nullptr;
    if (strategy!=nullptr) {
        activeStrategy = strategy;
    } else {
        defaultStrategy = std::make_unique<PDFWriter>(api);
        activeStrategy = defaultStrategy.get();
    }

    for (const auto &file : files) {
        activeStrategy->add_page(file);
    }
    switch (activeStrategy->write(output, "output")) {
        case NoPDFWriter:
            throw TesseractGlueException("missing pdf write strategy");
        case ReadError:
            throw TesseractGlueException("Read Error");
        case InitializationError:
            throw TesseractGlueException("Initialization Error");
        case ProcessingError:
            throw TesseractGlueException("Processing Error");
        case NoPagesGiven:
            throw TesseractGlueException("No Pages Given");
        case WriteError:
            throw TesseractGlueException("Write Error");
        case UnknownError:
            throw TesseractGlueException("Unknown Error");
        case Success:
            break;
    }
}