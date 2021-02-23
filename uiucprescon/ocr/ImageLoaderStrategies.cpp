//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#include <leptonica/allheaders.h>
#include "ImageLoaderStrategies.h"


std::shared_ptr<Image> ImageLoaderStrategyStandard::load(const std::string &filename){
    std::shared_ptr<Pix> imageData(pixRead(filename.c_str()), freePix);
    if(!imageData){
        throw std::runtime_error("Unable to load " + filename);
    }
    return std::make_shared<Image>(imageData);
}

void ImageLoaderStrategyStandard::freePix(Pix *src) {
    pixDestroy(&src);
}
