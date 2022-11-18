#ARG manylinux_image=quay.io/pypa/manylinux2014_x86_64
#FROM ${manylinux_image} as base_python
#ENV PATH=/opt/python/cp39-cp39/bin:/opt/python/cp38-cp38/bin:/opt/python/cp37-cp37m/bin:/opt/python/cp36-cp36m/bin:/opt/python/cp35-cp35m/bin:$PATH
#RUN mkdir -p /.cache/pip && \
#    chmod -R 777 /.cache
#ARG TARGETARCH
#COPY ci/docker/linux/package/conan/$TARGETARCH/profile.ini /conan/.conan/profiles/default
#COPY ci/docker/shared/conan/remotes.json  /conan/.conan/remotes.json
#RUN pip3 install conan cmake ninja
#ENV CONAN_USER_HOME=/conan
#RUN conan config init && \
#    conan config set general.revisions_enabled=1
#ARG PIP_EXTRA_INDEX_URL
#ARG PIP_INDEX_URL
#
#FROM base_python as conan_builder
#
#COPY conanfile.py /tmp/conanfile.py
#WORKDIR /conantest
#RUN conan install /tmp --build missing --build tesseract && \
#    LD_LIBRARY_PATH=/conantest/lib && $(conan info /tmp/conanfile.py --paths --package-filter="tesseract/*" | grep package_folder: | sed -e 's/[ \t]*package_folder: //' -e "s/$/\/bin\/tesseract/") --version > /tmp/results.txt && \
#    cat /tmp/results.txt && \
#    if grep -q libopenjp2 /tmp/results.txt; then echo "found it"; else >&2 echo "Tesseract was not built with openjpeg " ; exit 1; fi && \
#    conan remove "*" -b --src -f && \
#    conan remove --locks
#
#FROM base_python
#ADD conanfile.py /tmp/conanfile.py
#ENV CONAN_USER_HOME=/conan
#ENV CONAN_DEFAULT_PROFILE_PATH=/conan/.conan/profiles/default
#COPY --from=conan_builder /conan/.conan/ /conan/.conan/
##RUN ls -la /conan/ && exit 1
#
#RUN conan install /tmp --build outdated --no-import  && \
#    conan remove "*" -b --src -f && \
#    conan remove --locks && \
#    chmod -R 777 /conan
#ENV CONAN_COMPILER_VERSION=10
#ENV CONAN_COMPILER_LIBCXX=libstdc++11
#RUN python3 -m pip install build

ARG manylinux_image=quay.io/pypa/manylinux2014_x86_64
FROM ${manylinux_image} as base_python
ENV PATH=/opt/python/cp39-cp39/bin:/opt/python/cp38-cp38/bin:/opt/python/cp37-cp37m/bin:/opt/python/cp36-cp36m/bin:/opt/python/cp35-cp35m/bin:$PATH
RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
RUN python3 --version && python3 -m pip install conan
ARG TARGETARCH
COPY ci/docker/linux/package/conan/$TARGETARCH/profile.ini  /conan/.conan/profiles/default
COPY ci/docker/shared/conan/remotes.json  /conan/.conan/remotes.json
ADD conanfile.py /tmp/conanfile.py
ENV CONAN_USER_HOME=/conan
RUN conan config home
RUN conan install /tmp --build  missing --no-import  && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 /conan

RUN python3 -m pip install build