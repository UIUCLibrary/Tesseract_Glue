//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#include "ImageLoaderStrategies.h"
#include "fileLoader.h"
#include <memory>
#include <string>

namespace uiucprescon {
    namespace ocr {
        class Image;

        std::shared_ptr<Image> ImageLoader::loadImage(const std::string &filename) {
            ImageLoaderStrategyStandard strategy;
            return strategy.load(filename);
        }

        std::shared_ptr<Image> ImageLoader::loadImage(const std::string &filename, abcImageLoaderStrategy &strategy) {
            return strategy.load(filename);
        }
    } // namespace ocr
}// namespace uiucprescon
