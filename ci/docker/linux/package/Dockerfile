FROM quay.io/pypa/manylinux2014_x86_64 as base_python
ENV PATH=/opt/python/cp39-cp39/bin:/opt/python/cp38-cp38/bin:/opt/python/cp37-cp37m/bin:/opt/python/cp36-cp36m/bin:/opt/python/cp35-cp35m/bin:$PATH
RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

FROM base_python as conan_builder
RUN pip3 install conan cmake ninja
COPY ci/docker/linux/package/conan/profile.ini  /conan/.conan/profiles/default
COPY ci/docker/shared/conan/remotes.json  /conan/.conan/remotes.json
ENV CONAN_USER_HOME=/conan
RUN conan config init && \
    conan config set general.revisions_enabled=1
COPY conanfile.py /tmp/conanfile.py
RUN conan install /tmp --build tesseract && \
    $(conan info /tmp/conanfile.py --paths --package-filter="tesseract/*" | grep package_folder: | sed -e 's/[ \t]*package_folder: //' -e "s/$/\/bin\/tesseract/") --version > /tmp/results.txt && \
    cat /tmp/results.txt && \
    if grep -q libopenjp2 /tmp/results.txt; then echo "found it"; else >&2 echo "Tesseract was not built with openjpeg " ; exit 1; fi && \
    conan remove "*" -b --src -f && \
    conan remove --locks

FROM base_python
RUN python3 --version && python3 -m pip install conan ninja
COPY ci/docker/linux/package/conan/profile.ini  /conan/.conan/profiles/default
COPY ci/docker/shared/conan/remotes.json  /conan/.conan/remotes.json
ADD conanfile.py /tmp/conanfile.py
ENV CONAN_USER_HOME=/conan
COPY --from=conan_builder /conan/.conan/ /conan/.conan/
RUN conan config init && \
    conan config set general.revisions_enabled=1

RUN conan install /tmp --build outdated --no-import  && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 /conan

RUN python3 -m pip install pep517 build
