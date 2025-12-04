#include "glue.h"
#include "Capabilities.h"
#include "glueExceptions.h"
#include "reader2.h"
#include "utils.h"

#include <memory>
#include <string>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

PYBIND11_MODULE(tesseractwrap, m,  pybind11::mod_gil_not_used()){
    pybind11::options options;
    options.enable_function_signatures();
    m.doc() = R"pbdoc(Wrapper to Tesseract's C++ API)pbdoc";

    // the classes need to be declared before the functions, otherwise you get a generic_type is already registered error
    pybind11::class_<Image, std::shared_ptr<Image>>(m, "Image", pybind11::module_local())
            .def_property_readonly("w", &Image::get_w)
            .def_property_readonly("h", &Image::get_h);

    pybind11::class_<Reader2>(m, "Reader")
            .def(pybind11::init<const std::string &, const std::string &>())
            .def("get_ocr", &Reader2::get_ocr_from_image);

    // ================================================================================================================
    m.def("tesseract_version", &tesseract_version, "Get the version of tesseract being used");
    m.def("get_image_lib_versions", [](){
        return Capabilities::ImagelibVersions();
        }, "Get the version of image libraries being used");

    m.def("load_image", &load_image, "Load image file");
    pybind11::register_exception<TesseractGlueException>(m, "TesseractGlueException", PyExc_RuntimeError);


}
