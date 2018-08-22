Examples
========

To get the OCR data from an image you need do the following

    1. Create an  :attr:`uiucprescon.ocu.Engine` object the points to the tesseract data files
    2. Get a :attr:`uiucprescon.ocu.Reader` object from the Engine
    3. Use the :meth:`Reader.read` method to generate text

.. TODO: Make this make sense

.. code-block:: python

    from uiucprescon import ocr

    ocr.Engine
    reader = ocr.Reader(language_code="eng", tesseract_data_path=tessdata_eng)

    test_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")

    text = reader.read(test_image)
