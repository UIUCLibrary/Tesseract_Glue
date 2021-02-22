#ifndef GLUE_H
#define GLUE_H
#include <string>
#include "Image.h"

int dummy();

int give_five();

std::string read_image(const std::string &source);
std::shared_ptr<Image> load_image(const std::string &source);
int set_tessdata(const std::string &path);

#endif /* GLUE_H */
