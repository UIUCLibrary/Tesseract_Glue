ARG manylinux_image=quay.io/pypa/manylinux2014_x86_64
ARG CONAN_USER_HOME=/conan
FROM ${manylinux_image} as base_python
ENV PATH=/opt/python/cp311-cp311/bin:/opt/python/cp310-cp310/bin:/opt/python/cp39-cp39/bin:/opt/python/cp38-cp38/bin:/opt/python/cp37-cp37m/bin:/opt/python/cp36-cp36m/bin:/opt/python/cp35-cp35m/bin:$PATH
RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
COPY requirements/requirements-conan.txt /tmp/requirements-conan.txt
RUN python3 --version && python3 -m pip install --no-cache-dir -r /tmp/requirements-conan.txt
ARG TARGETARCH
ARG CONAN_USER_HOME
COPY ci/docker/linux/package/conan/$TARGETARCH/profile.ini  ${CONAN_USER_HOME}/.conan/profiles/default
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY conanfile.py /tmp/conanfile.py
RUN conan config init && \
    conan config set general.revisions_enabled=1
WORKDIR /conantest
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN conan install /tmp --build missing --build tesseract && \
    LD_LIBRARY_PATH=/conantest/lib && $(conan info /tmp/conanfile.py --paths --package-filter="tesseract/*" | grep package_folder: | sed -e 's/[ \t]*package_folder: //' -e "s/$/\/bin\/tesseract/") --version > /tmp/results.txt && \
    cat /tmp/results.txt && \
    if grep -q libopenjp2 /tmp/results.txt; then echo "found it"; else >&2 echo "Tesseract was not built with openjpeg " ; exit 1; fi && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 ${CONAN_USER_HOME}

RUN python3 -m pip install --no-cache-dir build
