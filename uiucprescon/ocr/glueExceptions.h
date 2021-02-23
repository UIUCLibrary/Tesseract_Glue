//
// Created by Borchers, Henry Samuel on 2/23/21.
//

#ifndef OCR_GLUEEXCEPTIONS_H
#define OCR_GLUEEXCEPTIONS_H
#include <exception>
#include <string>
class TesseractGlueException: public std::exception{
    const std::string message;
public:
    explicit TesseractGlueException(std::basic_string<char> message) noexcept;
};


#endif //OCR_GLUEEXCEPTIONS_H
