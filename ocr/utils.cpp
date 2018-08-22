#include "utils.h"
#include <baseapi.h>

std::string tesseract_version(){
    return tesseract::TessBaseAPI::Version();
}