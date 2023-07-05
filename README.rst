===============
uiucprescon.ocr
===============

Wrapper around Google Tesseract for Python.



Master Branch:

.. image:: https://jenkins.library.illinois.edu/buildStatus/icon?job=OpenSourceProjects/Tesseract_Glue/master
    :target: https://jenkins.library.illinois.edu/job/OpenSourceProjects/job/Tesseract_Glue/job/master/


.. Note::
   This package requires building of C/C++ extension modules for Python which needs to be built before it can be
   used. See instructions below on how to build.

Building
--------

Requirements
____________
    * Python 3.8 or greater
    * C/C++ compiler

Instructions
____________

    1. Install "build" package into your python environment
    2. Run build command ::

        python -m build

    This generates a whl and tar.gz file in the ./dist/ directory and can be used to install into your Python
    environment.
