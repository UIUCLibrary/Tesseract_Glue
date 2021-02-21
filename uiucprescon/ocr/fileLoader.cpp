//
// Created by Borchers, Henry Samuel on 2/21/21.
//

#include <leptonica/allheaders.h>
#include "ImageLoaderStrategies.h"
#include "fileLoader.h"

Pix *ImageLoader::loadImage(const std::string &filename, abcImageLoaderStrategy &strategy){
    return strategy.load(filename);
}


Pix *ImageLoader::loadImage(const std::string &filename){
    ImageLoaderStrategyStandard strategy;
    return loadImage(filename, strategy);
}


//////////////

//do something with
//if(image == nullptr){
//FILE *fp;
//if ((fp = fopenReadStream(image_filename.c_str())) == nullptr) {
//throw std::runtime_error("image file not found: " + image_filename);
//}
//image = pixReadWithHint(image_filename.c_str(), 0);
////        pix = pixReadStreamJp2k(fp, 1, NULL, 0, 0)) == NULL)
//l_int32 format,  pw, ph, pbps,  pspp, piscmap, w, h ,spp, bps;
//int rc = findFileFormatStream(fp, &format);
//if(format == IFF_JP2){
//Pix *pix = nullptr;
//pix = pixReadStreamJp2k(fp, 1, NULL, 0, 0);
//std::cout << "dsafasdf";
//}
//
////            int ret = readHeaderJp2k(image_filename.c_str(), &w, &h, &bps, &spp);
//////            int ret = readHeaderJpeg(image_filename.c_str(), &w, &h, &spp, NULL, NULL);
//////            pixReadStreamJp2k
////
////        }
////        PIX *pix = pixReadStream(fp, 0);
//
//////        l_int32 w, h, bps, spp, pformat;
////        int rc = pixReadHeader(image_filename.c_str(), &format, &pw, &ph, &pbps,  &pspp, &piscmap);
//return "";
//}
