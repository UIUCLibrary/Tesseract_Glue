//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#ifndef OCR_IMAGELOADERSTRATEGIES_H
#define OCR_IMAGELOADERSTRATEGIES_H

#include <leptonica/allheaders.h>

#include <string>
#include "Image.h"
class abcImageLoaderStrategy {

public:
    virtual ~abcImageLoaderStrategy() = default;
    virtual std::shared_ptr<Image> load(const std::string &filename) = 0;
};

class ImageLoaderStrategyStandard : public abcImageLoaderStrategy {
private:
    static void freePix(Pix *src);
public:
    std::shared_ptr<Image> load(const std::string &filename) override;
};

#endif //OCR_IMAGELOADERSTRATEGIES_H
