"""Reader for extracting text information."""
import abc
import os
from uiucprescon.ocr import tesseractwrap  # type: ignore


class AbsReader(metaclass=abc.ABCMeta):
    """Baseclass used for implementing various reader types."""

    def __init__(self, language_code, tesseract_data_path) -> None:
        """Reader object for interacting with tesseract and the image.

        Args:
            language_code:
            tesseract_data_path:
        """
        super().__init__()

        def is_lang_in_path(lang) -> bool:
            data_file = "{}.traineddata".format(lang)
            return os.path.exists(os.path.join(tesseract_data_path, data_file))

        if not is_lang_in_path(language_code):
            raise FileNotFoundError(
                "No \"{}\" language file located in \"{}\"".format(
                    language_code, tesseract_data_path))

        if not is_lang_in_path("osd"):
            raise FileNotFoundError(
                "osd file not located in \"{}\"".format(tesseract_data_path))

        self._tesseract_data_path = tesseract_data_path

        self.language_code = language_code
        self._reader = tesseractwrap.Reader(self._tesseract_data_path,
                                            self.language_code)

    @abc.abstractmethod
    def read(self, file: str):
        """Read a image file for text information."""
        raise NotImplementedError


class Reader(AbsReader):
    """Reading the text from an image file.

    Note:
        A Reader object should not be generated directly. Instead, it should be
        constructed using the Engine class's :meth:`Engine.get_reader` method.

    """

    def read(self, file: str):
        """Generate text from an image.

        Args:
            file: File path to an image

        Returns:
            Text extracted from an image

        """
        return self._reader.get_ocr(file)
