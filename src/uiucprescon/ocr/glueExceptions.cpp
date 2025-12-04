//
// Created by Borchers, Henry Samuel on 2/23/21.
//

#include "glueExceptions.h"
#include <string>

TesseractGlueException::TesseractGlueException(const std::string &message) noexcept: message(message) {}
