#include "reader.h"
#include <iostream>
#include <leptonica/allheaders.h>
#include <string>

Reader::Reader(const std::string &tessdata, const std::string &lang):language(lang), tessdata(tessdata)
{
    if (0 != tess.Init(tessdata.c_str(), "eng")){
        std::cout << "OCRTesseract: Could not initialize tesseract." << std::endl;
        this->good = false;
    }

    this->good = true;
}

Reader::~Reader()
{
    tess.End();
}

bool Reader::isGood(){
    return this->good;
}

std::string Reader::get_ocr(const std::string &image_filename){
    if(!this->good){
        return "";
    }
    
    Pix *image = pixRead(image_filename.c_str());

    tess.SetImage(image);
    std::string result = std::string(tess.GetUTF8Text());

    pixDestroy(&image);
    return result;
}