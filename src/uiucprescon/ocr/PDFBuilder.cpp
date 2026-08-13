//
// Created by Borchers, Henry Samuel on 7/17/26.
//
#include "PDFBuilder.h"

#include "Image.h"
#include "OCRApi.h"
#include "exceptions.h"
#include "fileLoader.h"

#include <tesseract/renderer.h>


#include <iostream>
#include <memory>
#include <string>

#if defined(__APPLE__) && defined(__MACH__)
#include <Availability.h>
#endif

#if defined(__APPLE__) && defined(__MACH__) && __MAC_OS_X_VERSION_MIN_REQUIRED < 101500
#include <unistd.h>
#else
#include <filesystem>
#endif

namespace uiucprescon::ocr {
    bool is_renderer_ready_to_use(const tesseract::TessPDFRenderer* renderer) {
        return (renderer != nullptr) && renderer->happy();
    }
    PDFBuilder::PDFBuilder(const std::string& file_path, const std::shared_ptr<OCRApi>& api, const std::string& title) :
        m_pdf_file_path(file_path), m_api(api), m_title(title) {}

    namespace {
        bool file_exists(const std::string& file_path) {
#if defined(__APPLE__) && defined(__MACH__) && (__MAC_OS_X_VERSION_MIN_REQUIRED < 101500)
            // Even though macOS 10.14 is no longer supported, Pybind11 by defaults to macOS 10.14
            // compatibility which doesn't have std::filesystem. To get around this, we have to check if the user
            // has access to the file instead. This is not as good of a solution as std::filesystem::exists, but it
            // is what is available on this platform.

            // For more information, look for the comment located in
            // pybind11.setup_helpers.Pybind11Extension.cxx_std()
            return (access(file_path.c_str(), F_OK) == 0);
#else
            return std::filesystem::exists(file_path);
#endif
        }
    } // namespace

    PDFBuilderStatusCodes PDFBuilder::do_add_page(const std::string& file_path) {
        using enum PDFBuilderStatusCodes;
        if (!file_exists(file_path)) {
            return FileNotFound;
        }
        const auto image = ImageLoader::loadImage(file_path);
        return this->add_page(*image);
    }

    bool PDFBuilder::renderer_is_ready() const noexcept { return is_renderer_ready_to_use(m_renderer.get()); }

    bool PDFBuilder::process_page(std::shared_ptr<Pix> pix, int page_index, const std::string& filename,
                                  const char* retry_config, int timeout_millisec) const {
        return m_api->ProcessPage(pix.get(), page_index, filename.c_str(), retry_config, timeout_millisec,
                                  m_renderer.get());
    }

    std::unique_ptr<tesseract::TessPDFRenderer> PDFBuilder::create_renderer() const noexcept {
        return std::make_unique<tesseract::TessPDFRenderer>(
            (m_pdf_file_path.ends_with(".pdf") ? m_pdf_file_path.substr(0, m_pdf_file_path.length() - 4)
                                               : m_pdf_file_path)
                .c_str(),
            m_api->get_tesseract_data_path(), false);
    }

    PDFBuilderStatusCodes PDFBuilder::do_add_page(const Image& image, const std::string& file_path) {
        using enum PDFBuilderStatusCodes;
        if (!renderer_is_ready()) {
            std::cerr << "tesseract renderer not initialized. Was the file opened?" << std::endl;
            return InitializationError;
        }
        try {
            if (!this->process_page(image.getPix(), m_page_index, file_path, nullptr, 0)) {
                return ProcessingError;
            }
            m_page_index++;
        }
        catch (const OCRException& e) {
            std::cerr << "Unable to read image file. Reason: " << e.what() << std::endl;
            return ReadError;
        }
        return Success;
    }

    PDFBuilderStatusCodes PDFBuilder::open() {
        this->m_renderer = create_renderer();
        using enum PDFBuilderStatusCodes;
        if (!renderer_is_ready()) {
            std::cerr << "Unable to initialize tesseract renderer." << std::endl;
            return InitializationError;
        }
        m_renderer->BeginDocument(m_title.c_str());
        m_page_index = 0;
        return Success;
    }

    void PDFBuilder::close() {
        if (this->m_renderer) {
            this->m_renderer->EndDocument();
            this->m_renderer.reset();
        }
    }
} // namespace uiucprescon::ocr
