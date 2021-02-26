//
// Created by Borchers, Henry Samuel on 2/25/21.
//

#include "Capabilities.h"
#include <leptonica/allheaders.h>
std::string Capabilities::ImagelibVersions() {
    std::unique_ptr<char> ptr(getImagelibVersions(), std::default_delete<char>());
    return std::string(ptr.get());
}
//
//std::map<const std::string, std::string> Capabilities::ImagelibVersions2() {
//    std::map<const std::string, std::string> data;
//
//    #define STRINGIFY(x) #x
//    #define TOSTRING(x) STRINGIFY(x)
//
//    #ifdef LIBJP2K_HEADER
//    data["jp2k"] = TOSTRING(LIBJP2K_HEADER);
////    #include LIBJP2K_HEADER
////    char *version = opj_version();
//    #endif
//
//    #undef STRINGIFY
//    #undef TOSTRING
//    return data;
//}
