===============
uiucprescon.ocr
===============

Wrapper around Google Tesseract for Python.



Master Branch:

.. image:: https://jenkins-prod.library.illinois.edu/buildStatus/icon?job=open%20source/uiucprescon.ocr/master
    :target: https://jenkins-prod.library.illinois.edu/job/open%20source/job/uiucprescon.ocr/job/master/


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

Building Portable Python Wheels For Mac
---------------------------------------

Since this package links to Tesseract library, to make sure that these files are generated in a portable manner and
will run on other machines, please use the included shell script (scripts/build_mac_wheel.sh) provided to generate
them.


.. code-block:: console

    ./scripts/build_mac_wheel.sh .
