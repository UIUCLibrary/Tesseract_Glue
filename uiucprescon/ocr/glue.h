#ifndef GLUE_H
#define GLUE_H
#include <string>
#include "Image.h"

std::shared_ptr<Image> load_image(const std::string &source);

#endif /* GLUE_H */
