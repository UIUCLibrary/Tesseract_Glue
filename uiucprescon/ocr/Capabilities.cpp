//
// Created by Borchers, Henry Samuel on 2/25/21.
//
#include <memory>
#include "Capabilities.h"
#include <leptonica/allheaders.h>
std::string Capabilities::ImagelibVersions() {
    std::unique_ptr<char> ptr(getImagelibVersions(), std::default_delete<char>());
    return std::string(ptr.get());
}
