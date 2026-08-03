#ifndef GLUE_H
#define GLUE_H

#include "Image.h"
#include "PDFBuilder.h"

#include <string>

namespace uiucprescon::glue {
    std::shared_ptr<ocr::Image> load_image(const std::string& source);
    void pdf_builder_add_pages(ocr::IPDFBuilder& self, const std::string& file_path);
    void pdf_builder_add_pages(ocr::IPDFBuilder& self, const ocr::Image& image, const std::string& source = "");
    void pdf_builder_open(ocr::IPDFBuilder& self);
    ocr::Image pixScaleToSize(const ocr::Image& image, int targetWidth, int targetHeight);
} // namespace uiucprescon::glue

#endif /* GLUE_H */
