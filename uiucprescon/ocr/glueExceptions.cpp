//
// Created by Borchers, Henry Samuel on 2/23/21.
//
#include <utility>

#include "glueExceptions.h"


TesseractGlueException::TesseractGlueException(std::basic_string<char> message): message(std::move(message)) {}

const char *TesseractGlueException::what() const noexcept {
    return message.c_str();
}
