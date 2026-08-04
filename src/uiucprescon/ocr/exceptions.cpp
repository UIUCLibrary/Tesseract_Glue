//
// Created by Borchers, Henry Samuel on 2/23/21.
//

#include "exceptions.h"

#include <iostream>
#include <string>

namespace uiucprescon {
    namespace glue {
        TesseractGlueException::TesseractGlueException(const std::string& message) noexcept :
            UIUCPresconException(message) {}
    } // namespace glue
    namespace ocr {
        OCRException::OCRException(const std::string& message) noexcept : UIUCPresconException(message) {}
    } // namespace ocr
} // namespace uiucprescon
