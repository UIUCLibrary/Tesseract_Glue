import abc
from . import reader
from uiucprescon.ocr import tesseractwrap  # type: ignore


class AbsEngine(metaclass=abc.ABCMeta):
    def __init__(self, data_set_path) -> None:
        self.data_set_path = data_set_path

    @abc.abstractmethod
    def get_reader(self, lang: str) -> reader.AbsReader:
        pass

    @abc.abstractmethod
    def get_version(self) -> str:
        pass


class Engine(AbsEngine):
    """The engine for driving the ocr processing"""

    def get_reader(self, lang: str) -> reader.AbsReader:
        """ Builder method for creating reader objects for a specific language

        Args:
            lang: letter code that represents the language for a tesseract data
                set

        Returns:
            Constructs a Reader object which can be used for extracting text from
            and image.

        """
        ocr_reader = reader.Reader(lang, self.data_set_path)
        return ocr_reader

    def get_version(self) -> str:
        """ Check the version of Tesseract linked to"""
        return tesseractwrap.tesseract_version()
