#include "Image.h"
#include "fileLoader.h"
#include "glueExceptions.h"
#include "reader2.h"
#include <iostream>
#include <memory>
#include <string>

using std::endl;
using std::cerr;

Reader2::Reader2(const std::string &tessdata, const std::string &lang):
    language(lang),
    tessdata(tessdata)
{
    if (0 != tess.Init(tessdata.c_str(), lang.c_str())){
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
    return std::string (std::unique_ptr<char[]>(tess.GetUTF8Text(), std::default_delete<char[]>()).get());
}
