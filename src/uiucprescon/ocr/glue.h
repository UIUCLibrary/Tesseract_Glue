#ifndef GLUE_H
#define GLUE_H

#include "Image.h"
#include "PDFBuilder.h"

#include <string>
#include <vector>


namespace uiucprescon {
    namespace glue {
        std::shared_ptr<ocr::Image> load_image(const std::string& source);
        void pdf_builder_add_pages(ocr::IPDFBuilder& self, const std::string& file_path);
        void pdf_builder_add_pages(ocr::IPDFBuilder& self, const ocr::Image& image, const std::string& source = "");
        void pdf_builder_open(ocr::IPDFBuilder& self);
    } // namespace glue
} // namespace uiucprescon

#endif /* GLUE_H */
