//
// Created by Borchers, Henry Samuel on 7/14/26.
//

#include "fileLoader.h"
#include "Image.h"
#include "OCRApi.h"
#include "pdf_writer.h"

#include <tesseract/baseapi.h>
#include <tesseract/renderer.h>

#include <cstddef>
#include <iostream>
#include <memory>
#include <string>
#include <vector>


bool TesseractPDFWriteStrategy::ProcessPage(
    const OCRApi &api,
    Pix *pix,
    int page_index,
    const char *filename,
    const char *retry_config,
    int timeout_millisec,
    tesseract::TessResultRenderer *renderer){
    return api.ProcessPage(pix, page_index, filename, retry_config, timeout_millisec, renderer);
}

PDFWriteErrorCodes TesseractPDFWriteStrategy::BeginDocument(const std::string &title, const StartDocumentCallback &callback) {
    if (!callback(title.c_str())) {
        std::cerr << "Unable to begin tesseract document." << std::endl;
        return PDFWriteErrorCodes::WriteError;
    }
    return PDFWriteErrorCodes::Success;
}

PDFWriteErrorCodes TesseractPDFWriteStrategy::EndDocument(const EndDocumentCallback &callback) {
    if (!callback()) {
        return PDFWriteErrorCodes::UnknownError;
    }
    return PDFWriteErrorCodes::Success;
};

std::shared_ptr<Image> TesseractPDFWriteStrategy::loadImage(const std::string &filename) {
    return ImageLoader::loadImage(filename);
}


std::unique_ptr<tesseract::TessPDFRenderer>
TesseractPDFWriteStrategy::makeRenderer(const std::string &output_filename, const char *dataPath) {
    auto renderer =  std::make_unique<tesseract::TessPDFRenderer>(
        (
            output_filename.ends_with(".pdf") ? output_filename.substr(0, output_filename.length() - 4): output_filename
        ).c_str(),
        dataPath,
        false
    );
    if (!renderer || !renderer->happy()) {
        std::cerr << "Unable to initialize tesseract renderer." << std::endl;
        return nullptr;
    }
    return renderer;
}


PDFWriteErrorCodes TesseractPDFWriteStrategy::generatePDF(const std::string &output_filename,
                                                          const std::vector<std::string> &files, std::shared_ptr<OCRApi> api) {
    return generatePDF(output_filename, files, api, "");
};


PDFWriteErrorCodes TesseractPDFWriteStrategy::generatePDF(const std::string& output_filename, const std::vector<std::string> &files, std::shared_ptr<OCRApi> api, const std::string &title) {
    using enum PDFWriteErrorCodes;
    if(!api){
        return NoPDFWriter;
    }
    const auto renderer = this->makeRenderer(output_filename, api->get_tesseract_data_path());

    if (const auto return_code = BeginDocument(title, [&renderer](const char *_title){return renderer->BeginDocument(_title);}); return_code != PDFWriteErrorCodes::Success) {
        return return_code;
    }
    for (constexpr size_t index = 0; const auto& file : files) {
        const auto image = this->loadImage(file);
        if (!image) {
            std::cerr << "Unable to read image file: " << file  << std::endl;
            return ReadError;
        }
        const bool success = this->ProcessPage(*api, image->getPix().get(), index, file.c_str(), nullptr, 0, renderer.get());
        if (!success) {
            return ProcessingError;
        }
    }
    if (const auto return_code = EndDocument([&renderer]{return renderer->EndDocument();}); return_code != PDFWriteErrorCodes::Success) {
        return return_code;
    }
    return Success;
}

PDFWriter::PDFWriter(
    std::shared_ptr<OCRApi> api,
    const std::shared_ptr<AbstractPDFWriteStrategy> &writeStrategy): pdf_writer(writeStrategy == nullptr ? std::make_shared<TesseractPDFWriteStrategy>():writeStrategy), m_api(api)  {
}



PDFWriter::PDFWriter(std::shared_ptr<OCRApi> api, const std::vector<std::string> &pages,
                     const std::shared_ptr<AbstractPDFWriteStrategy> &writeStrategy): pdf_writer(writeStrategy), images(pages), m_api(api) {}

size_t PDFWriter::size() const {
    return this->images.size();
}

void PDFWriter::add_page(const std::string &filename) {
    this->images.push_back(filename);
}

PDFWriteErrorCodes PDFWriter::do_write(const std::string &filename, const std::string &title) const {
    using enum PDFWriteErrorCodes;
    if (this->images.empty()) {
        return NoPagesGiven;
    }

    if (this->pdf_writer == nullptr) {
        return NoPDFWriter;
    }
    if (!m_api) {
        return NoPDFWriter;
    }
    return this->pdf_writer->generatePDF(filename, this->images, m_api, title);
}
