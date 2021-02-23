//
// Created by Borchers, Henry Samuel on 2/22/21.
//

#include <memory>
#include <utility>
#include "Image.h"

Image::Image(std::shared_ptr <Pix> image) : image(std::move(image)) {}

std::shared_ptr<Pix> Image::getPix() const{
    return this->image;
}

int Image::get_w() const{
    if(image == nullptr){
        return 0;
    }
    return image->w;
}

int Image::get_h() const{
    if(image == nullptr){
        return 0;
    }
    return image->h;
}
