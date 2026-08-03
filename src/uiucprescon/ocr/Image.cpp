//
// Created by Borchers, Henry Samuel on 2/22/21.
//

#include "Image.h"
#include <leptonica/allheaders.h>
#include <memory>
#include <utility>
namespace {
    std::shared_ptr<Pix> copyPix(std::shared_ptr<Pix> pix) {
        return std::shared_ptr<Pix>(pixCopy(nullptr, pix.get()), [](Pix* pixData) { pixDestroy(&pixData); });
    }
} // namespace
namespace uiucprescon::ocr {

    Image::Image(std::shared_ptr<Pix> image) : image(std::move(image)) {}

    Image::Image(const Image& other) {
        if (other.image != nullptr) {
            this->image = copyPix(other.image);
        }
    }

    std::shared_ptr<Pix> Image::getPix() const { return this->image; }

    Image& Image::operator=(const Image& other) {
        if (this != &other) {
            this->image = copyPix(other.image);
        }
        return *this;
    }

    int Image::get_w() const {
        if (image == nullptr) {
            return 0;
        }
        return pixGetWidth(image.get());
    }

    int Image::get_h() const {
        if (image == nullptr) {
            return 0;
        }
        return pixGetHeight(image.get());
    }
} // namespace uiucprescon::ocr
