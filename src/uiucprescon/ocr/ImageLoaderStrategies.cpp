//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#include "ImageLoaderStrategies.h"
#include "Image.h"
#include "exceptions.h"

#include <leptonica/allheaders.h>

#include <memory>
#include <string>

struct Pix;

namespace uiucprescon {
    namespace ocr {
        std::shared_ptr<Image> ImageLoaderStrategyStandard::load(const std::string& filename) {
            const std::shared_ptr<Pix> imageData(pixRead(filename.c_str()), freePix);
            if (!imageData) {
                throw OCRException("Unable to load " + filename);
            }
            return std::make_shared<Image>(imageData);
        }

        void ImageLoaderStrategyStandard::freePix(Pix* src) {
            if (src != nullptr) {
                pixDestroy(&src);
            }
        }
    } // namespace ocr
} // namespace uiucprescon
