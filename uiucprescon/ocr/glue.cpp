#include <memory>
#include "Image.h"
#include "glue.h"
#include "fileLoader.h"
using namespace std;

std::shared_ptr<Image> load_image(const string &source) {
    return ImageLoader::loadImage(source);
}
