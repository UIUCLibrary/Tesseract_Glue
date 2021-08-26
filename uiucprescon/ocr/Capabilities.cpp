//
// Created by Borchers, Henry Samuel on 2/25/21.
//
#include "Capabilities.h"
#include <leptonica/allheaders.h>
#include <memory>
std::string Capabilities::ImagelibVersions() {
    std::unique_ptr<char> ptr(getImagelibVersions(), std::default_delete<char>());
    return std::string(ptr.get());
}
