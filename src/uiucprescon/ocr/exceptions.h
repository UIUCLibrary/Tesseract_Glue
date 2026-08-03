//
// Created by Borchers, Henry Samuel on 2/23/21.
//

#ifndef EXCEPTIONS_H
#define EXCEPTIONS_H
#include <stdexcept>
#include <string>

namespace uiucprescon {
    class UIUCPresconException: public std::runtime_error{
        // std::string message;
    public:
        using std::runtime_error::runtime_error;
        // explicit UIUCPresconException(const std::string &message) noexcept;
        // const char *what() const noexcept override {
        //     return message.c_str();
        // };
    };
    namespace glue {
        // class TesseractGlueException final: public std::runtime_error {
        class TesseractGlueException final: public UIUCPresconException {
        public:
            explicit TesseractGlueException(const std::string &message) noexcept;
        };
    } // namespace glue
    namespace ocr {
        class OCRException final: public UIUCPresconException{
        public:
            explicit OCRException(const std::string &message) noexcept;
        };
    } // namespace ocr
} // namespace uiucprescon

#endif //EXCEPTIONS_H
