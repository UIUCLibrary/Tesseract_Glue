#include "Image.h"
#include "reader2.h"
#include <string>
#include <iostream>
#include <memory>
#include "fileLoader.h"
#include "glueExceptions.h"

using std::endl;
using std::cerr;

Reader2::Reader2(const std::string &tessdata, const std::string &lang):
    language(lang),
    tessdata(tessdata)
{
    if (tess.Init(tessdata.c_str(), lang.c_str())){
        cerr << "OCRTesseract: Could not initialize tesseract." << endl;
        this->good = false;
        return;
    }
    tess.SetPageSegMode(tesseract::PSM_AUTO_OSD);

    this->good = true;
}


bool Reader2::isGood() const{
    return this->good;
}

std::string Reader2::get_ocr(const std::string &image_filename){
    const std::shared_ptr<Image> image = ImageLoader::loadImage(image_filename);
    return get_ocr_from_image(image);
}

std::string Reader2::get_ocr_from_image(const std::shared_ptr<Image> &image) {
    if(!this->good){
        return "";
    }

    tess.SetImage(image->getPix().get());
    tess.Recognize(nullptr);
    std::unique_ptr<tesseract::ResultIterator> ri(tess.GetIterator());
    tesseract::PageIteratorLevel level = tesseract::RIL_WORD;

    auto deleter = [](char *p){
        delete[] p;
    };
    if(ri != nullptr){
        do {
            const std::unique_ptr<char, decltype(deleter)> word(ri->GetUTF8Text(tesseract::RIL_WORD), deleter);
            float conf = ri->Confidence(level);
        } while(ri->Next(level));

    }
    std::unique_ptr<char, decltype(deleter)> data(tess.GetUTF8Text(), deleter);
    auto result = std::string(data.get());
    return result;
}
