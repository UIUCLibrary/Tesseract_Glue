ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}
RUN pip install conan wheel
ADD conanfile.py /tmp/conanfile.py
RUN conan install /tmp/ --build  missing --no-import