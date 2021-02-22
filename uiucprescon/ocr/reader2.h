#pragma once

#include <tesseract/baseapi.h>
#include <string>

class Reader2
{
private:
   tesseract::TessBaseAPI tess;
   std::string language;
   std::string tessdata;
   bool good;
public:
    Reader2(const std::string &tessdata, const std::string &lang);
    ~Reader2();
    std::string get_ocr(const std::string &image_filename);
    bool isGood();
};

