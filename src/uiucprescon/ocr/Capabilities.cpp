//
// Created by Borchers, Henry Samuel on 2/25/21.
//
#include "Capabilities.h"
#include <leptonica/allheaders.h>
#include <string>

std::string Capabilities::ImagelibVersions() noexcept {
    return std::string(getImagelibVersions());
}
