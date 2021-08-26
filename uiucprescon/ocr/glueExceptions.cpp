//
// Created by Borchers, Henry Samuel on 2/23/21.
//
#include <utility>

#include "glueExceptions.h"

TesseractGlueException::TesseractGlueException(const std::string &message) noexcept: message(message) {}
//TesseractGlueException::TesseractGlueException(const std::string &message) noexcept: message(std::move(message)) {}
