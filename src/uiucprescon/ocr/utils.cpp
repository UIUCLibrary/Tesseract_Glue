#include "utils.h"
#include <string>
#include <tesseract/baseapi.h>

namespace uiucprescon::ocr {
    std::string tesseract_version() { return tesseract::TessBaseAPI::Version(); }
} // namespace uiucprescon::ocr
