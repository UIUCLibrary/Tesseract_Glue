//
// Created by Borchers, Henry Samuel on 2/22/21.
//

#include "Image.h"
#include <leptonica/allheaders.h>
#include <memory>
#include <utility>
Image::Image(std::shared_ptr <Pix> image) : image(std::move(image)) {}

std::shared_ptr<Pix> Image::getPix() const{
    return this->image;
}

int Image::get_w() const{
    if(image == nullptr){
        return 0;
    }
    return pixGetWidth(image.get());
}

int Image::get_h() const{
    if(image == nullptr){
        return 0;
    }
    return pixGetHeight(image.get());
}
