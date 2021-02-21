#include "reader2.h"
#include <string>
#include <iostream>
#include <leptonica/allheaders.h>
#include "fileLoader.h"

using std::endl;
using std::cerr;

Reader2::Reader2(const std::string &tessdata, const std::string &lang):language(lang), tessdata(tessdata)
{
    tess = new tesseract::TessBaseAPI();
    if (tess->Init(tessdata.c_str(), lang.c_str())){
        cerr << "OCRTesseract: Could not initialize tesseract." << endl;
        this->good = false;
    }
    tess->SetPageSegMode(tesseract::PSM_AUTO_OSD);

    this->good = true;
}

Reader2::~Reader2()
{
    tess->End();
}

bool Reader2::isGood(){
    return this->good;
}

std::string Reader2::get_ocr(const std::string &image_filename){
    if(!this->good){
        return "";
    }

    Pix *image = ImageLoader::loadImage(image_filename);

    tess->SetImage(image);
    tess->Recognize(0);
    tesseract::ResultIterator* ri = tess->GetIterator();
    tesseract::PageIteratorLevel level = tesseract::RIL_WORD;
    if(ri != 0){
        do {

            const char* word = ri->GetUTF8Text(tesseract::RIL_WORD);
            float conf = ri->Confidence(level);
//            std::cout << conf << std::endl;
        } while(ri->Next(level));

    }
    std::string result = std::string(tess->GetUTF8Text());
    pixDestroy(&image);
    return result;
}