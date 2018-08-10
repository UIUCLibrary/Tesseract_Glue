import abc
from ocr import tesseractwrap  # type: ignore

# TODO: remove hard coded data directory
TESS_DATA = r"C:\Users\hborcher\PycharmProjects\ocr\build\tests\tessdata"


# TODO: Create a configuration for looking up the location for tesseract data
# This will most likely be a factory or a builder pattern

class AbsReader(metaclass=abc.ABCMeta):

    def __init__(self, language_code) -> None:
        super().__init__()

        self._tesseract_data_path = TESS_DATA

        self.language_code = language_code
        self._reader = tesseractwrap.Reader(self._tesseract_data_path,
                                            self.language_code)

    @abc.abstractmethod
    def read(self, file):
        pass


class Reader(AbsReader):
    def read(self, file):
        return self._reader.get_ocr(file)
