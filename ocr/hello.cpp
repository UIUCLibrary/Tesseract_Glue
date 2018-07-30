#include <iostream>
#include <baseapi.h>

using namespace std;

int dummy(){
    cout << "hello world\n";
    tesseract::TessBaseAPI tess;

    if (tess.Init("./tessdata", "eng"))
    {
        std::cout << "OCRTesseract: Could not initialize tesseract." << std::endl;
        return 1;
    }

    return 0;
}