//
// Created by Borchers, Henry Samuel on 7/20/26.
//

#ifndef OCR_OCR_API_H
#define OCR_OCR_API_H

#include <memory>

#include <tesseract/baseapi.h>

namespace uiucprescon {
    namespace ocr {
        class OCRApi {
            std::unique_ptr<tesseract::TessBaseAPI> api = nullptr;
        public:
            OCRApi();

            static std::shared_ptr<OCRApi> create(const std::string &tessdata_path, const std::string &lang_code);
            bool ProcessPage(Pix *pix, int page_index, const char *filename,
                             const char *retry_config, int timeout_millisec,
                             tesseract::TessResultRenderer *renderer) const;
            const char *get_tesseract_data_path() const;

            void SetPageSegMode(tesseract::PageSegMode mode);
            tesseract::PageSegMode GetPageSegMode() const;

            void set_image(Pix *pix);
            void End();

            int recognize(tesseract::ETEXT_DESC *monitor);
            char *get_utf8_text();
            ~OCRApi();

        };
    } // namespace ocr
} //namespace uiucprescon

#endif //OCR_OCR_API_H
