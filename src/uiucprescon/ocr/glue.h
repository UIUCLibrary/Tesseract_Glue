#ifndef GLUE_H
#define GLUE_H

#include "Image.h"
#include "OCRApi.h"
#include "PDFBuilder.h"

#include <string>


namespace uiucprescon::glue {
    std::shared_ptr<ocr::Image> load_image(const std::string& source);
    void pdf_builder_add_pages(ocr::IPDFBuilder& self, const std::string& file_path);
    void _pdf_builder_add_pages(ocr::PDFBuilder& self, const std::string& file_path);
    void pdf_builder_add_pages(ocr::IPDFBuilder& self, const ocr::Image& image, const std::string& source = "");
    void _pdf_builder_add_pages(ocr::PDFBuilder& self, const ocr::Image& image, const std::string& source = "");
    void pdf_builder_open(ocr::IPDFBuilder& self);
    void _pdf_builder_open(ocr::PDFBuilder& self);
    ocr::PDFBuilder _pdf_builder_init(const std::string& file_path, const std::shared_ptr<ocr::OCRApi>& api,
                                      const std::string& title);
    ocr::PDFBuilder* _pdf_builder_enter(ocr::PDFBuilder* self);
    ocr::Image pixScaleToSize(const ocr::Image& image, int targetWidth, int targetHeight);
    void react_pdf_builder_open_return_code(PDFBuilderStatusCodes return_code);
} // namespace uiucprescon::glue

#endif /* GLUE_H */
