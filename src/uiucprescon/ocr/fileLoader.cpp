//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#include "ImageLoaderStrategies.h"
#include "Image.h"
#include "fileLoader.h"
#include <memory>
#include <string>


std::shared_ptr<Image> ImageLoader::loadImage(const std::string &filename) {
    ImageLoaderStrategyStandard strategy;
    return strategy.load(filename);
}

std::shared_ptr<Image> ImageLoader::loadImage(const std::string &filename, abcImageLoaderStrategy &strategy) {
    return strategy.load(filename);
}
