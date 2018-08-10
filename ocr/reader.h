#include <baseapi.h>
#include <string>

class Reader
{
private:
   tesseract::TessBaseAPI tess;
   std::string language;
   std::string tessdata;
   bool good;
public:
    Reader(const std::string &tessdata, const std::string &lang);
    ~Reader();
    std::string get_ocr(const std::string &image_filename);
    bool isGood();
};

