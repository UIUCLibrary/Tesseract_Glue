//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#include <leptonica/allheaders.h>
#include "ImageLoaderStrategies.h"
#include "fileLoader.h"

Pix *ImageLoader::loadImage(const std::string &filename, abcImageLoaderStrategy &strategy){
    return strategy.load(filename);
}


Pix *ImageLoader::loadImage(const std::string &filename){
    ImageLoaderStrategyStandard strategy;
    return loadImage(filename, strategy);
}
