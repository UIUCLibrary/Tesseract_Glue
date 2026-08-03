//
// Created by Borchers, Henry Samuel on 7/22/26.
//

#include "OCRApi.h"
#include <catch2/catch_test_macros.hpp>

#include <tesseract/publictypes.h>

namespace ocr = uiucprescon::ocr;

TEST_CASE("OCRApi") {
    SECTION("PageSegMode") {
        auto api = ocr::OCRApi::create(TESS_DATA, "eng");
        api->SetPageSegMode(tesseract::PageSegMode::PSM_SINGLE_BLOCK);
        REQUIRE(api->GetPageSegMode() == tesseract::PageSegMode::PSM_SINGLE_BLOCK);

    }
}