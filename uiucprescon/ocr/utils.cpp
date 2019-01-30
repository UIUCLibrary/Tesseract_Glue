#include "utils.h"
#include <tesseract/baseapi.h>

std::string tesseract_version(){
    return tesseract::TessBaseAPI::Version();
}