Examples
========

OCR Test from Image
___________________

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


Create Searchable PDF
---------------------

To create a searchable PDF do the following.

    1. Create an :py:obj:`OCRApi<uiucprescon.ocr.OCRApi>` object that points
       to the path that the tesseract data files are stored and the language
       code to use.
    2. Create an :py:obj:`PDFBuilder<uiucprescon.ocr.PDFBuilder>` object that
       with a new pdf file name and the OCR API instance.
    3. Create an open context by using the manager protocol in the PDFBuilder
       object. This will open a new pdf file to write images pages to.
    4. Use the add_page() method to add images pages to the pdf file. This
       will immediately perform OCR on the image and write it directly to the
       file pdf file.
    5. When the context is closed, the pdf file will be closed.

.. code-block:: python

    from uiucprescon import ocr

    tesseract_api = ocr.OCRApi("c:/tessdata", language_code="eng")
    pdf_file_name = "my_scanned_book.pdf"

    with ocr.PDFBuilder(pdf_file_name, tesseract_api) as pdf_builder:
        text = pdf_builder.add_page("page1.tif")
        text = pdf_builder.add_page("page2.tif")

    # At this point, the pdf will be finished writing to and
    #  the file handle will be closed