Examples
========

To get the OCR data from an image you need do the following

    1. Create an :py:obj:`Engine<uiucprescon.ocr.Engine>` object that points to the
       path that the tesseract data files are stored.
    2. Get a :py:obj:`Reader<uiucprescon.ocr.Reader>` object using the newly created
       engine instance using its :meth:`Engine.get_reader` method.
    3. Use the reader object's :py:meth:`read()<uiucprescon.ocr.Reader.read>` method to generate text.

.. code-block:: python

    from uiucprescon import ocr

    tesseract_engine = ocr.Engine("c:/tessdata")
    reader = tesseract_engine.get_reader(lang="eng")
    text = reader.read("IlliniLore_1944_00000011.tif")
