#include<pybind11/pybind11.h>
#include "glue.h"
#include "reader.h"

PYBIND11_MODULE(tesseractwrap, m){
    pybind11::options options;
    options.enable_function_signatures();
    m.doc() = R"pbdoc(Wrapper to Tesseract's C++ API)pbdoc";

    m.def("give_five", &give_five, "Gives you the number 5");
    m.def("read_image", &read_image, "reads an image");
    m.def("set_tessdata", &set_tessdata, "sets the tessdata path");
	pybind11::class_<Reader>(m, "Reader").def(pybind11::init<const std::string &, const std::string &>()).def("get_ocr", &Reader::get_ocr);
}
