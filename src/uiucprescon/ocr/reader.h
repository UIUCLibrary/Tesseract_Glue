#pragma once

#include <string>
#include <tesseract/baseapi.h>

namespace uiucprescon {
    namespace ocr {
        class Reader {
            tesseract::TessBaseAPI tess;
            std::string language;
            std::string tessdata;

        public:
            Reader(const std::string& tessdata, const std::string& lang);
            ~Reader();
            std::string get_ocr(const std::string& image_filename);
        };
    } // namespace ocr
} // namespace uiucprescon
