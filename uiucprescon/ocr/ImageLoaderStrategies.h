//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#ifndef OCR_IMAGELOADERSTRATEGIES_H
#define OCR_IMAGELOADERSTRATEGIES_H


#include <leptonica/environ.h>
#include <leptonica/pix.h>
#include <string>

class abcImageLoaderStrategy {

public:
    virtual ~abcImageLoaderStrategy() = default;
    virtual Pix * load(const std::string &filename) = 0;
};

class ImageLoaderStrategyStandard : public abcImageLoaderStrategy {

public:
    Pix *load(const std::string &filename) override;
};

#endif //OCR_IMAGELOADERSTRATEGIES_H
