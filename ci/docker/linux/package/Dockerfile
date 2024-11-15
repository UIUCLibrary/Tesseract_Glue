ARG manylinux_image=quay.io/pypa/manylinux2014_x86_64
ARG CONAN_USER_HOME=/conan

FROM ${manylinux_image} AS base_python
ENV PATH=/opt/python/cp311-cp311/bin:/opt/python/cp310-cp310/bin:/opt/python/cp39-cp39/bin:/opt/python/cp38-cp38/bin:/opt/python/cp37-cp37m/bin:/opt/python/cp36-cp36m/bin:/opt/python/cp35-cp35m/bin:$PATH
RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ARG CONAN_USER_HOME
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY conanfile.py /tmp/conanfile.py
COPY requirements-dev.txt /tmp/requirements-dev.txt
WORKDIR /conantest
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN python3 -m venv venv && \
    . ./venv/bin/activate \
    pip install --disable-pip-version-check uv && \
    uv pip install -r /tmp/requirements-dev.txt && \
    conan config init && \
    conan config set general.revisions_enabled=1 && \
    conan profile update settings.compiler.version=$(cc -dumpfullversion -dumpversion | grep -oE  "^([0-9]+(\.)?)([0-9]+?)") default &&  \
    conan install -pr:b=default --build missing --build tesseract /tmp && \
    LD_LIBRARY_PATH=/conantest/lib && $(conan info /tmp/conanfile.py --paths --package-filter="tesseract/*" | grep package_folder: | sed -e 's/[ \t]*package_folder: //' -e "s/$/\/bin\/tesseract/") --version > /tmp/results.txt && \
    cat /tmp/results.txt && \
    if grep -q libopenjp2 /tmp/results.txt; then echo "found it"; else >&2 echo "Tesseract was not built with openjpeg " ; exit 1; fi && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    uv cache prune && \
    rm -rf venv && \
    chmod -R 777 ${CONAN_USER_HOME}

