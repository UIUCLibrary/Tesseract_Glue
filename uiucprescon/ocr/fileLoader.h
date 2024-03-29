//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#ifndef OCR_FILELOADER_H
#define OCR_FILELOADER_H

#include "Image.h"
#include "ImageLoaderStrategies.h"
#include <string>

class ImageLoader{
public:
    static std::shared_ptr<Image> loadImage(const std::string &filename);
    static std::shared_ptr<Image> loadImage(const std::string &filename, abcImageLoaderStrategy &strategy);

};
#endif //OCR_FILELOADER_H
