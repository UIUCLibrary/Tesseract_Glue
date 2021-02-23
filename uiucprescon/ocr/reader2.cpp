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


bool Reader2::isGood(){
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
    tesseract::ResultIterator* ri = tess.GetIterator();
    tesseract::PageIteratorLevel level = tesseract::RIL_WORD;
    if(ri != nullptr){
        do {

            const char* word = ri->GetUTF8Text(tesseract::RIL_WORD);
            float conf = ri->Confidence(level);
        } while(ri->Next(level));

    }
    auto result = std::string(tess.GetUTF8Text());
    return result;
}
