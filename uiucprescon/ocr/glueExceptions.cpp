//
// Created by Borchers, Henry Samuel on 2/23/21.
//
#include <utility>

#include "glueExceptions.h"


TesseractGlueException::TesseractGlueException(std::basic_string<char> message) noexcept: message(std::move(message)) {}
