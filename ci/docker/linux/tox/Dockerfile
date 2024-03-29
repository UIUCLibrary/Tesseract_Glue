ARG TARGETARCH=amd64
ARG CONAN_USER_HOME=/conan
ARG PIP_DOWNLOAD_CACHE=/.cache/pip
ARG PIPX_HOME=/pipx
FROM ubuntu:22.04 AS wheel_builder_base
COPY ci/docker/linux/tox/apt-packages.txt /tmp/apt-packages.txt
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && \
    apt-get install -y software-properties-common gpg-agent --no-install-recommends && \
    add-apt-repository ppa:deadsnakes/ppa && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata && \
    apt-get update && \
     < /tmp/apt-packages.txt xargs apt-get install -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache


FROM wheel_builder_base AS conan_builder
ARG CONAN_USER_HOME
COPY requirements/requirements-dev-freeze.txt /tmp/requirements-dev-freeze.txt
RUN python3 -m pip install pip --upgrade && pip3 install --no-cache-dir -r /tmp/requirements-dev-freeze.txt
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY conanfile.py /tmp/conanfile.py
COPY ci/docker/linux/tox/update_conan_compiler.py  /tmp/update_conan_compiler.py
RUN conan config init && \
    conan config set general.revisions_enabled=1 && \
    conan profile update settings.compiler.version=$(cc -dumpfullversion -dumpversion | grep -oE  "^([0-9]+(\.)?)([0-9]+?)") default && \
    python3 /tmp/update_conan_compiler.py ${CONAN_USER_HOME}/.conan/settings.yml gcc $(cc -dumpfullversion -dumpversion | grep -oE  "^([0-9]+(\.)?)([0-9]+?)") && \
    conan install /tmp -pr:b=default --build outdated --build=openjpeg --no-import && \
    conan remove "*" -b --src -f && \
    conan remove --locks

# ==============================================================================

FROM wheel_builder_base
ARG CONAN_USER_HOME
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY requirements/ /tmp/requirements/requirements/
COPY requirements-dev.txt /tmp/requirements/requirements-dev.txt
RUN python3 -m pip install pip --upgrade && pip3 install --no-cache-dir  -r /tmp/requirements/requirements-dev.txt


COPY --from=conan_builder ${CONAN_USER_HOME}/.conan/ ${CONAN_USER_HOME}/.conan/
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY conanfile.py /tmp/conanfile.py

RUN conan install /tmp --build  missing --no-import -pr:b=default && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 ${CONAN_USER_HOME}

ENV CONAN_USER_HOME=${CONAN_USER_HOME}
ARG PIP_DOWNLOAD_CACHE
RUN mkdir -p ${PIP_DOWNLOAD_CACHE} && \
    chmod -R 777 ${PIP_DOWNLOAD_CACHE}

ENV PIP_DOWNLOAD_CACHE=${PIP_DOWNLOAD_CACHE}

ARG PIPX_HOME
ENV PIPX_HOME=${PIPX_HOME}
ENV PIPX_BIN_DIR=${PIPX_HOME}/bin
RUN python3 -m pip install --no-cache-dir pipx && \
    pipx ensurepath && \
    mkdir -p $PIPX_HOME  && chmod -R 777 $PIPX_HOME

RUN PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install 'devpi-client<7.0'

WORKDIR /src
CMD ["tox", "--workdir", "/tmp/tox/",  "-p=auto", "--parallel--safe-build", "--recreate"]
