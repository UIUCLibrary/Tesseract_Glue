
#include <iostream>
// FIXME: These headers should not be root path.
// They should be located in the header directory of their package.
// For example: tesseract/baseapi.h and leptonica/allheaders.h
#include <baseapi.h>
#include <allheaders.h>

#include "glue.h"

using namespace std;

string tessdata;

int dummy(){
    cout << "hello world\n";
    tesseract::TessBaseAPI tess;

    if (tess.Init(tessdata.c_str(), "eng"))
//    if (tess.Init("./tessdata", "eng"))
    {
        std::cout << "OCRTesseract: Could not initialize tesseract." << std::endl;
        return 1;
    }

    return 0;
}

int give_five(){
    // dummy();
    return 5;
}
int set_tessdata(const string &path){
    tessdata = path;
    return 0;
}

// TODO: Follow examples here -> https://github.com/tesseract-ocr/tesseract/wiki/APIExample
std::string read_image(const string &source){
    tesseract::TessBaseAPI api;
    api.Init(tessdata.c_str(), "eng");
    Pix *image = pixRead(source.c_str());

    api.SetImage(image);
    string result = string(api.GetUTF8Text());
    api.End();
    pixDestroy(&image);
    return result;
}