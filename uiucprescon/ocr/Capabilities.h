//
// Created by Borchers, Henry Samuel on 2/25/21.
//

#ifndef OCR_CAPABILITIES_H
#define OCR_CAPABILITIES_H

#include <string>
#include <map>

class Capabilities {
public:
    static std::string ImagelibVersions();
    static std::map<const std::string, std::string> ImagelibVersions2();
};


#endif //OCR_CAPABILITIES_H
