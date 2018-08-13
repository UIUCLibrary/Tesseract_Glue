import abc
import os

from ocr import tesseractwrap  # type: ignore

class AbsReader(metaclass=abc.ABCMeta):

    def __init__(self, language_code, tesseract_data_path) -> None:
        super().__init__()

        def is_lang_in_path() ->bool:
            data_file = "{}.traineddata".format(language_code)
            return os.path.exists(os.path.join(tesseract_data_path, data_file))

        if not is_lang_in_path():
            raise FileNotFoundError(
                "No \"{}\" language file located in \"{}\"".format(
                    language_code, tesseract_data_path))

        self._tesseract_data_path = tesseract_data_path

        self.language_code = language_code
        self._reader = tesseractwrap.Reader(self._tesseract_data_path,
                                            self.language_code)



    @abc.abstractmethod
    def read(self, file):
        pass


class Reader(AbsReader):

    def read(self, file):
        return self._reader.get_ocr(file)
