//
// Created by Borchers, Henry Samuel on 2/22/21.
//

#ifndef OCR_IMAGE_H
#define OCR_IMAGE_H
#include <leptonica/alltypes.h>
#include <memory>
class Image {
private:
    std::shared_ptr<Pix> image;
public:
    Image(std::shared_ptr<Pix> image);
    std::shared_ptr<Pix> getPix();

    int get_w();
    int get_h();
};


#endif //OCR_IMAGE_H
