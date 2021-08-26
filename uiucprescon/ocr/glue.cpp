#include "Image.h"
#include "fileLoader.h"
#include "glue.h"
#include <memory>
using namespace std;

std::shared_ptr<Image> load_image(const string &source) {
    return ImageLoader::loadImage(source);
}
