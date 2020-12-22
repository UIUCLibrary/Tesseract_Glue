"""Engine/middleware for connecting to Google tesseract & ocr data files."""

import abc
from uiucprescon.ocr import tesseractwrap  # type: ignore
from . import reader


class AbsEngine(metaclass=abc.ABCMeta):
    """Baseclass for engines."""

    def __init__(self, data_set_path: str) -> None:
        """Create an OCR engine.

        Args:
            data_set_path:
                Path to the ocr data sets.
        """
        self.data_set_path = data_set_path

    @abc.abstractmethod
    def get_reader(self, lang: str) -> reader.AbsReader:
        """Get reader of a specific language.

        Args:
            lang: language code

        Returns:
            reader object to use with images

        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_version(self) -> str:
        """Get the version of Tesseract being used.

        Returns:
            Tesseract version number

        """
        raise NotImplementedError


class Engine(AbsEngine):
    """The engine for driving the ocr processing."""

    def get_reader(self, lang: str) -> reader.AbsReader:
        """Builder method for creating reader objects for a specific language.

        Args:
            lang: letter code that represents the language for a tesseract data
                set.

        Returns:
            Constructs a Reader object which can be used for extracting text
            from and image.

        """
        ocr_reader = reader.Reader(lang, self.data_set_path)
        return ocr_reader

    def get_version(self) -> str:
        """Check the version of Tesseract that this package is linked to.

        An example value might be the string "3.05.02".

        """
        return tesseractwrap.tesseract_version()
