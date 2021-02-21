//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#ifndef OCR_FILELOADER_H
#define OCR_FILELOADER_H

#include <leptonica/environ.h>
#include <leptonica/pix.h>
#include <string>
#include "ImageLoaderStrategies.h"


class ImageLoader{
public:
    static Pix* loadImage(const std::string &filename, abcImageLoaderStrategy &strategy);
    static Pix* loadImage(const std::string &filename);

};
#endif //OCR_FILELOADER_H
