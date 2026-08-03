#pragma once
#include "Image.h"
#include "OCRApi.h"

#include <memory>
#include <string>

namespace uiucprescon {
    namespace ocr {
        class Reader2 {
            std::shared_ptr<OCRApi> m_api;

        public:
            explicit Reader2(std::shared_ptr<OCRApi> api);
            std::string get_ocr(const std::string& image_filename) const;
            std::string get_ocr_from_image(const std::shared_ptr<Image>& image) const;
        };
    } // namespace ocr
} // namespace uiucprescon
