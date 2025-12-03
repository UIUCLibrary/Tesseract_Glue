#include "Image.h"
#include "fileLoader.h"
#include "glue.h"
#include <memory>
using std::string;
using std::shared_ptr;

shared_ptr<Image> load_image(const string &source) {
    return ImageLoader::loadImage(source);
}
