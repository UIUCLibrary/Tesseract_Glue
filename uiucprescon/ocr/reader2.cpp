#include "reader2.h"
#include <string>
#include <iostream>
#include <leptonica/allheaders.h>
#include "fileLoader.h"

using std::endl;
using std::cerr;

Reader2::Reader2(const std::string &tessdata, const std::string &lang):
    language(lang),
    tessdata(tessdata)
{
    if (tess.Init(tessdata.c_str(), lang.c_str())){
        cerr << "OCRTesseract: Could not initialize tesseract." << endl;
        this->good = false;
    }
    tess.SetPageSegMode(tesseract::PSM_AUTO_OSD);

    this->good = true;
}


bool Reader2::isGood(){
    return this->good;
}

std::string Reader2::get_ocr(const std::string &image_filename){
    if(!this->good){
        return "";
    }

    Pix *image = ImageLoader::loadImage(image_filename);
    if (image == nullptr){
        throw std::runtime_error("Unable to load " + image_filename);
    }

    tess.SetImage(image);
    tess.Recognize(nullptr);
    tesseract::ResultIterator* ri = tess.GetIterator();
    tesseract::PageIteratorLevel level = tesseract::RIL_WORD;
    if(ri != nullptr){
        do {

            const char* word = ri->GetUTF8Text(tesseract::RIL_WORD);
            float conf = ri->Confidence(level);
        } while(ri->Next(level));

    }
    auto result = std::string(tess.GetUTF8Text());
    pixDestroy(&image);
    return result;
}