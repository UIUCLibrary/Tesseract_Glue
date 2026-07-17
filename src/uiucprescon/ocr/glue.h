#ifndef GLUE_H
#define GLUE_H

#include "Image.h"
#include "PDFBuilder.h"
#include "pdf_writer.h"

#include <string>
#include <vector>


class OCRApi;

std::shared_ptr<Image> load_image(const std::string &source);
void create_pdf(const std::vector<std::string> &files, const std::string &output, const std::shared_ptr<OCRApi> &api, IPDFWriter *strategy=nullptr);
void pdf_builder_add_pages(IPDFBuilder &self, const std::string &file_path);
void pdf_builder_open(IPDFBuilder &self);
#endif /* GLUE_H */
