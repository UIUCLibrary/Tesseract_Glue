#include "utils.h"
#include <string>
#include <tesseract/baseapi.h>

namespace uiucprescon {
    namespace ocr {
        std::string tesseract_version() { return tesseract::TessBaseAPI::Version(); }
    } // namespace ocr
} // namespace uiucprescon
