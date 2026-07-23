#include "Image.h"
#include "OCRApi.h"
#include "fileLoader.h"
#include "reader2.h"

#include <tesseract/publictypes.h>

#include <algorithm>
#include <cctype>
#include <memory>
#include <string>
namespace {
    bool string_contains_no_text(const std::string &str) {
        return std::all_of(std::begin(str), std::end(str), [](const char character) { return std::isspace(character); });
    }
} // namespace

Reader2::Reader2(std::shared_ptr<OCRApi> api): m_api(api){
    m_api->SetPageSegMode(tesseract::PSM_AUTO_OSD);

}

std::string Reader2::get_ocr(const std::string &image_filename) const{
    const std::shared_ptr<Image> image = ImageLoader::loadImage(image_filename);
    return get_ocr_from_image(image);
}

std::string Reader2::get_ocr_from_image(const std::shared_ptr<Image> &image) const{
    m_api->set_image(image->getPix().get());
    m_api->recognize(nullptr);
    auto result =  std::string (std::unique_ptr<char[]>(m_api->get_utf8_text(), std::default_delete<char[]>()).get());
    return string_contains_no_text(result) ?  std::string() : result;
}

