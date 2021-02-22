//
// Created by Borchers, Henry Samuel on 2/22/21.
//

#include <memory>
#include <utility>
#include "Image.h"

Image::Image(std::shared_ptr <Pix> image) : image(std::move(image)) {}

std::shared_ptr<Pix> Image::getPix() {
    return this->image;
}

int Image::get_w() {
    return image->w;
}

int Image::get_h() {
    return image->h;
}
