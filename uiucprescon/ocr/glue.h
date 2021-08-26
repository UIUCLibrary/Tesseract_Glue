#ifndef GLUE_H
#define GLUE_H
#include "Image.h"
#include <string>

std::shared_ptr<Image> load_image(const std::string &source);

#endif /* GLUE_H */
