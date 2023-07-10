ARG TARGETARCH=amd64
ARG COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES=9.4
ARG CONAN_USER_HOME=/conan
ARG PIP_DOWNLOAD_CACHE=/.cache/pip
FROM ubuntu:20.04 as wheel_builder_base
COPY ci/docker/linux/tox/apt-packages.txt /tmp/apt-packages.txt
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && \
    apt-get install -y software-properties-common --no-install-recommends && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    < /tmp/apt-packages.txt xargs apt-get install -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache


FROM wheel_builder_base as conan_builder
ARG CONAN_USER_HOME
COPY ci/docker/linux/tox/requirements-conan-build.txt /tmp/
COPY requirements/requirements_conan.txt /tmp/requirements_conan.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements-conan-build.txt
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
ARG TARGETARCH
COPY ci/docker/linux/tox/conan/$TARGETARCH/profile.ini  ${CONAN_USER_HOME}/profiles/default
COPY conanfile.py /tmp/conanfile.py
RUN conan config init && \
    conan config set general.revisions_enabled=1

COPY ci/docker/linux/tox/update_conan_compiler.py  /tmp/update_conan_compiler.py
ARG COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES
RUN python3 /tmp/update_conan_compiler.py ${CONAN_USER_HOME}/.conan/settings.yml gcc $COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES

RUN conan install /tmp -pr:b=default --build outdated --build=openjpeg --no-import -s compiler.version=$COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES  && \
    conan remove "*" -b --src -f && \
    conan remove --locks

# ==============================================================================

FROM wheel_builder_base
ARG CONAN_USER_HOME
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY requirements/ /tmp/requirements
COPY ci/docker/linux/tox/requirements-conan-build.txt /tmp/requirements
RUN pip3 install --no-cache-dir  -r /tmp/requirements/requirements_tox.txt -r /tmp/requirements/requirements-conan-build.txt devpi-client twine


COPY --from=conan_builder ${CONAN_USER_HOME}/.conan/ ${CONAN_USER_HOME}/.conan/
ARG TARGETARCH

COPY ci/docker/linux/tox/conan/$TARGETARCH/profile.ini  ${CONAN_USER_HOME}/.conan/profiles/default
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY conanfile.py /tmp/conanfile.py

RUN conan config init && \
    conan config set general.revisions_enabled=1 && \
    conan profile update settings.compiler.libcxx=libstdc++11 default

ARG COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES
RUN conan install /tmp --build  missing --no-import -pr:b=default -s compiler.version=$COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 ${CONAN_USER_HOME}

ENV CONAN_USER_HOME=${CONAN_USER_HOME}
ARG PIP_DOWNLOAD_CACHE
RUN mkdir -p ${PIP_DOWNLOAD_CACHE} && \
    chmod -R 777 ${PIP_DOWNLOAD_CACHE}

ENV PIP_DOWNLOAD_CACHE=${PIP_DOWNLOAD_CACHE}

WORKDIR /src
CMD ["tox", "--workdir", "/tmp/tox/",  "-p=auto", "--parallel--safe-build", "--recreate"]
