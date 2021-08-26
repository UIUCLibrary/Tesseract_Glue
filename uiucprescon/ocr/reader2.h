#pragma once
#include "Image.h"
#include <memory>
#include <string>
#include <tesseract/baseapi.h>

class Reader2
{
private:
   tesseract::TessBaseAPI tess = tesseract::TessBaseAPI();
   std::string language;
   std::string tessdata;
   bool good;
public:
    Reader2(const std::string &tessdata, const std::string &lang);
    std::string get_ocr(const std::string &image_filename);
    std::string get_ocr_from_image(const std::shared_ptr<Image> &image);
    [[nodiscard]] bool isGood() const;
};

