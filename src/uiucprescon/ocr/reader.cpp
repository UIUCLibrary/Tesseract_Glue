#include "reader.h"

#include <leptonica/allheaders.h>
#include <tesseract/baseapi.h>

#include <iostream>
#include <string>

namespace uiucprescon {
    namespace ocr {
        Reader::Reader(const std::string &tessdata, const std::string &lang):language(lang), tessdata(tessdata){
            if (0 != tess.Init(tessdata.c_str(), "eng")){
                std::cout << "OCRTesseract: Could not initialize tesseract." << std::endl;
            }
        }

        Reader::~Reader(){
            tess.End();
        }

        std::string Reader::get_ocr(const std::string &image_filename){

            Pix *image = pixRead(image_filename.c_str());

            tess.SetImage(image);
            auto result = std::string(tess.GetUTF8Text());

            pixDestroy(&image);
            return result;
        }
    } // namespace ocr
} // namespace uiucprescon
