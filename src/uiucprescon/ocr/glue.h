#ifndef GLUE_H
#define GLUE_H

#include "Image.h"
#include "PDFBuilder.h"

#include <string>
#include <vector>


class OCRApi;

std::shared_ptr<Image> load_image(const std::string &source);
void pdf_builder_add_pages(IPDFBuilder &self, const std::string &file_path);
void pdf_builder_open(IPDFBuilder &self);
#endif /* GLUE_H */
