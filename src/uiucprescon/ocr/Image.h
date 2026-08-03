//
// Created by Borchers, Henry Samuel on 2/22/21.
//

#ifndef OCR_IMAGE_H
#define OCR_IMAGE_H

#include <memory>

struct Pix;

namespace uiucprescon::ocr {
    class Image {
        std::shared_ptr<Pix> image;

    public:
        explicit Image(std::shared_ptr<Pix> image);
        Image(const Image& other);
        ~Image() = default;
        Image(Image&& image) noexcept = default;
        Image& operator=(Image&& other) noexcept = default;
        Image& operator=(const Image& other);

        std::shared_ptr<Pix> getPix() const;
        int get_w() const;
        int get_h() const;
    };
} // namespace uiucprescon::ocr

#endif // OCR_IMAGE_H
