import abc
from . import reader
from ocr import tesseractwrap  # type: ignore


class AbsEngine(metaclass=abc.ABCMeta):
    def __init__(self, data_set_path) -> None:
        self.data_set_path = data_set_path

    @abc.abstractmethod
    def get_reader(self, lang) -> reader.AbsReader:
        pass

    @abc.abstractmethod
    def get_version(self) -> str:
        pass


class Engine(AbsEngine):

    def get_reader(self, lang) -> reader.AbsReader:
        ocr_reader = reader.Reader(lang, self.data_set_path)
        return ocr_reader

    def get_version(self) -> str:
        return tesseractwrap.tesseract_version()
