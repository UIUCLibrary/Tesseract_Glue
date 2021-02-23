#include<pybind11/pybind11.h>
#include "glue.h"
#include "reader2.h"
#include "utils.h"
#include <leptonica/allheaders.h>

PYBIND11_MODULE(tesseractwrap, m){
    pybind11::options options;
    options.enable_function_signatures();
    m.doc() = R"pbdoc(Wrapper to Tesseract's C++ API)pbdoc";

//    m.def("set_tessdata", &set_tessdata, "sets the tessdata path");
    m.def("tesseract_version", &tesseract_version, "Get the version of tesseract being used");
    pybind11::class_<Pix, std::shared_ptr<Pix>>(m, "Pix")
            .def(pybind11::init<>());
    pybind11::class_<Image, std::shared_ptr<Image>>(m, "Image")
            .def_property_readonly("w", &Image::get_w)
            .def_property_readonly("h", &Image::get_h)
            ;
    m.def("load_image", &load_image, "Load image file");
	pybind11::class_<Reader2>(m, "Reader")
	        .def(pybind11::init<const std::string &, const std::string &>())
	        .def("get_ocr", &Reader2::get_ocr_from_image)
	        ;
}
