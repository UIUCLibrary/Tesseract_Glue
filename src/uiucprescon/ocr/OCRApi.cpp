//
// Created by Borchers, Henry Samuel on 7/20/26.
//

#include "OCRApi.h"

#include <tesseract/baseapi.h>
#include <tesseract/publictypes.h>

#include <memory>
#include <string>

namespace uiucprescon {
    namespace ocr {

        OCRApi::OCRApi(): api(std::make_unique<tesseract::TessBaseAPI>()) {}

        std::shared_ptr<OCRApi> OCRApi::create(const std::string &tessdata_path, const std::string &lang_code) {
            auto ptr = std::make_shared<OCRApi>();
            ptr->api->Init(tessdata_path.c_str(), lang_code.c_str());
            return ptr;
        }

        bool OCRApi::ProcessPage(Pix *pix, int page_index, const char *filename, const char *retry_config, int timeout_millisec,
                                 tesseract::TessResultRenderer *renderer) const{
            return api->ProcessPage(pix, page_index, filename, retry_config, timeout_millisec, renderer);
        }

        const char * OCRApi::get_tesseract_data_path() const {
            if (!api) {
                return "";
            }
            return api->GetDatapath();
        }

        void OCRApi::SetPageSegMode(tesseract::PageSegMode mode) {
            api->SetPageSegMode(mode);
        }

        tesseract::PageSegMode OCRApi::GetPageSegMode() const {
            return api->GetPageSegMode();
        }

        void OCRApi::set_image(Pix *pix) {
            api->SetImage(pix);
        }

        void OCRApi::End() {
            api->End();
        }

        int OCRApi::recognize(tesseract::ETEXT_DESC *monitor) {
            return api->Recognize(monitor);
        }

        char * OCRApi::get_utf8_text() {
            return api->GetUTF8Text();
        }

        OCRApi::~OCRApi() {
            api->End();
        }
    } //namespace ocr
} //namespace uiucprescon
