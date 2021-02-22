//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#include <leptonica/allheaders.h>
#include "ImageLoaderStrategies.h"


std::shared_ptr<Image> ImageLoaderStrategyStandard::load(const std::string &filename){
    return std::make_shared<Image>(std::shared_ptr<Pix>(pixRead(filename.c_str()), freePix));
}

void ImageLoaderStrategyStandard::freePix(Pix *src) {
    pixDestroy(&src);
}
