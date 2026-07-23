#include "Capabilities.h"
#include "OCRApi.h"
#include "glue.h"
#include "glueExceptions.h"
#include "pdf_writer.h"
#include "reader2.h"
#include "utils.h"

#include <iostream>
#include <memory>
#include <string>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "PDFBuilder.h"
namespace  py = pybind11;

PYBIND11_MODULE(tesseractwrap, m, py::mod_gil_not_used()) {
    py::options options;
    py::register_exception<TesseractGlueException>(m, "TesseractGlueException");
    options.enable_function_signatures();
    m.doc() = R"pbdoc(Wrapper to Tesseract's C++ API)pbdoc";

    // the classes need to be declared before the functions, otherwise you get a generic_type is already registered error
    py::class_<Image, std::shared_ptr<Image>>(m, "Image", py::module_local())
            .def_property_readonly("w", &Image::get_w)
            .def_property_readonly("h", &Image::get_h);
    py::class_<OCRApi, std::shared_ptr<OCRApi>>(m, "OCRApi")
        .def(py::init(&OCRApi::create), py::arg("datapath"), py::arg("language_code"))
        .def_property_readonly("datapath", &OCRApi::get_tesseract_data_path);

    py::class_<Reader2>(m, "Reader")
        .def(
            py::init([](const std::string &tessdata, const std::string &language_code) {
                const auto api = OCRApi::create(tessdata, language_code);
                return Reader2(api);
            }),
            py::arg("tessdata"), py::arg("language_code"))
        .def("get_ocr", &Reader2::get_ocr_from_image);
    py::class_<PDFBuilder>(m, "PDFBuilder")
        .def(
            py::init([](const std::string &filename, const std::shared_ptr<OCRApi> &api, const std::string &title) {
                return PDFBuilder(filename, api, title);
            }),
            py::arg("filename"), py::arg("api"), py::arg("title") = std::string("")
        )
        .def("open", [](PDFBuilder &self){pdf_builder_open(self);})
        .def("close", &PDFBuilder::close)
        .def("add_page",[](PDFBuilder &self, const std::string &file_path){return pdf_builder_add_pages(self, file_path);})
        .def(
            "__exit__",
            [](PDFBuilder &self, const py::object& exc_type, const py::object& exc_value, const py::object& traceback) {
            self.close();
        })
        .def(
            "__enter__",
            [](PDFBuilder *self) {
                self->open();
                return self;
            },
            py::return_value_policy::reference)
    ;
    // ================================================================================================================
    m.def("tesseract_version", &tesseract_version, "Get the version of tesseract being used");
    m.def("get_image_lib_versions", [](){
        return Capabilities::ImagelibVersions();
        }, "Get the version of image libraries being used");

    m.def("load_image", &load_image, "Load image file");
    m.def("create_pdf", [](const std::vector<std::string> &files, const std::string &output, const std::shared_ptr<OCRApi> &api){create_pdf(files, output, api);}, "Create a pdf file");


}
