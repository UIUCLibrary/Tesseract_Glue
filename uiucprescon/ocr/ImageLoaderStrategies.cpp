//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#include <leptonica/allheaders.h>
#include "ImageLoaderStrategies.h"

Pix *ImageLoaderStrategyStandard::load(const std::string &filename) {
    return pixRead(filename.c_str());
}
