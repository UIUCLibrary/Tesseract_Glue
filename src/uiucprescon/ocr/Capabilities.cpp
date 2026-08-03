//
// Created by Borchers, Henry Samuel on 2/25/21.
//
#include "Capabilities.h"
#include <leptonica/allheaders.h>

#include <string>

namespace uiucprescon {
    namespace ocr {
        std::string Capabilities::ImagelibVersions() { return std::string(getImagelibVersions()); }
    } // namespace ocr
} // namespace uiucprescon
