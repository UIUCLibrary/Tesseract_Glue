//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#include "ImageLoaderStrategies.h"
#include "glueExceptions.h"
#include <leptonica/allheaders.h>

std::shared_ptr<Image> ImageLoaderStrategyStandard::load(const std::string &filename){
    std::shared_ptr<Pix> imageData(pixRead(filename.c_str()), freePix);
    if(!imageData){
        throw TesseractGlueException("Unable to load " + filename);
    }
    return std::make_shared<Image>(imageData);
}

void ImageLoaderStrategyStandard::freePix(Pix *src) {
    pixDestroy(&src);
}
