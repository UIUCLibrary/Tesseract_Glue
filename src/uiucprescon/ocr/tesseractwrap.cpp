#include "Capabilities.h"
#include "OCRApi.h"
#include "PDFBuilder.h"
#include "exceptions.h"
#include "glue.h"
#include "reader2.h"
#include "utils.h"

#include <iostream>
#include <memory>
#include <string>

#include <leptonica/alltypes.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;
namespace ocr = uiucprescon::ocr;
namespace glue = uiucprescon::glue;

PYBIND11_MODULE(tesseractwrap, m, py::mod_gil_not_used()) {
    py::options options;
    py::register_exception<glue::TesseractGlueException>(m, "TesseractGlueException");
    options.enable_function_signatures();
    m.doc() = R"pbdoc(Wrapper to Tesseract's C++ API)pbdoc";

    // the classes need to be declared before the functions, otherwise you get a generic_type is already registered
    // error
    py::class_<ocr::Image, std::shared_ptr<ocr::Image>>(m, "Image", py::module_local())
        .def_property_readonly("w", &ocr::Image::get_w)
        .def_property_readonly("h", &ocr::Image::get_h);
    py::class_<ocr::OCRApi, std::shared_ptr<ocr::OCRApi>>(m, "OCRApi", "OCR Api for tesseract API.")
        .def(py::init(&ocr::OCRApi::create), py::arg("datapath"), py::arg("language_code"))
        .def_property_readonly("datapath", &ocr::OCRApi::get_tesseract_data_path);

    py::class_<ocr::Reader2>(m, "Reader")
        .def(py::init([](const std::string& tessdata, const std::string& language_code) {
                 const auto api = ocr::OCRApi::create(tessdata, language_code);
                 return ocr::Reader2(api);
             }),
             py::arg("tessdata"), py::arg("language_code"))
        .def("get_ocr", &ocr::Reader2::get_ocr_from_image);
    py::class_<ocr::PDFBuilder>(m, "PDFBuilder", "PDFBuilder builder class.")
        .def(py::init([](const std::string& filename, const std::shared_ptr<ocr::OCRApi>& api,
                         const std::string& title) { return ocr::PDFBuilder(filename, api, title); }),
             py::arg("filename"), py::arg("api"), py::arg("title") = std::string(""))
        .def(
            "open", [](ocr::PDFBuilder& self) { glue::pdf_builder_open(self); }, "Open pdf file for write.")
        .def("close", &ocr::PDFBuilder::close, "Close open file.")
        .def(
            "add_page",
            [](ocr::PDFBuilder& self, const std::string& file_path) { glue::pdf_builder_add_pages(self, file_path); },
            py::arg("file_path"), "Add image to pdf")
        .def(
            "add_page",
            [](ocr::PDFBuilder& self, const ocr::Image& image, const std::string& source) {
                glue::pdf_builder_add_pages(self, image, source);
            },
            py::arg("image"), py::arg("source_file") = "", "Add image to pdf")
        .def("__exit__",
             [](ocr::PDFBuilder& self, const py::object& /*exc_type*/, const py::object& /*exc_value*/,
                const py::object& /*traceback*/) { self.close(); })
        .def(
            "__enter__",
            [](ocr::PDFBuilder* self) {
                self->open();
                return self;
            },
            py::return_value_policy::reference);
    // ================================================================================================================
    m.def("tesseract_version", &ocr::tesseract_version, "Get the version of tesseract being used");
    m.def("get_image_lib_versions", &ocr::Capabilities::ImagelibVersions,
          "Get the version of image libraries being used");
    m.def("load_image", &glue::load_image, "Load image file");
}
