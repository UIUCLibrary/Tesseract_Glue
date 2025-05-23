ARG PYTHON_VERSION=3.11

# If you want to use a diffrent remote for Conan, such as a proxy. Set the CONAN_CENTER_PROXY_V1_URL
# Not this is only for building the image. The actual conan center proxy URL is set in the remotes.json file.
ARG CONAN_CENTER_PROXY_V1_URL

# PIP Cache directory. Change this only if you need to override the default location.
ARG PIP_DOWNLOAD_CACHE=/.cache/pip

# UV Cache directory. Change this only if you need to override the default location.
ARG UV_CACHE_DIR=/.cache/uv


ARG CONAN_USER_HOME=/conan
FROM python:${PYTHON_VERSION} AS base_python
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update -y &&  \
    apt-get install -y --no-install-recommends ca-certificates git clang-tidy && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache

FROM base_python AS conan_builder
ARG CONAN_USER_HOME
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
COPY requirements-dev.txt /tmp/requirements-dev.txt
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY conanfile.py /tmp/conanfile.py
ARG CONAN_CENTER_PROXY_V1_URL
ARG UV_CACHE_DIR
ARG PIP_DOWNLOAD_CACHE
RUN --mount=type=cache,target=${PIP_DOWNLOAD_CACHE} \
    --mount=type=cache,target=${UV_CACHE_DIR} \
    python3 -m venv venv && \
    ./venv/bin/pip --disable-pip-version-check install uv && \
    ./venv/bin/uvx --constraint=/tmp/requirements-dev.txt --with cmake conan config init && \
    ./venv/bin/uvx --constraint=/tmp/requirements-dev.txt --with cmake conan config set general.revisions_enabled=1 && \
    ./venv/bin/uvx --constraint=/tmp/requirements-dev.txt --with cmake conan profile update settings.compiler.version=$(cc -dumpfullversion -dumpversion | grep -oE  "^([0-9]+(\.)?)([0-9]+?)") default && \
    if [ -n "${CONAN_CENTER_PROXY_V1_URL}" ]; then \
    echo 'Using a proxy for conan center' && \
        cp ${CONAN_USER_HOME}/.conan/remotes.json /tmp/remotes.json && \
        ./venv/bin/uvx --constraint=/tmp/requirements-dev.txt --with cmake conan remote remove conan-center && \
        ./venv/bin/uvx --constraint=/tmp/requirements-dev.txt --with cmake conan remote add conan-center ${CONAN_CENTER_PROXY_V1_URL}; \
    fi && \
    ./venv/bin/uvx --constraint=/tmp/requirements-dev.txt --with cmake conan install /tmp --build outdated --build=openjpeg --no-import -pr:b=default && \
    ./venv/bin/uvx --constraint=/tmp/requirements-dev.txt --with cmake conan remove "*" -b --src -f && \
    ./venv/bin/uvx --constraint=/tmp/requirements-dev.txt --with cmake conan remove --locks && \
    rm -rf venv && \
    if [ -n "${CONAN_CENTER_PROXY_V1_URL}" ]; then \
        mv -f /tmp/remotes.json ${CONAN_USER_HOME}/.conan/remotes.json; \
    fi

#==============================================================================

FROM base_python AS SONAR_BUILDER
ARG SONAR_USER_HOME

RUN case $(uname -m) in \
    x86_64) URL=https://sonarcloud.io/static/cpp/build-wrapper-linux-x86.zip ;; \
    aarch64) URL=https://sonarcloud.io/static/cpp/build-wrapper-linux-aarch64.zip ;; \
    esac; \
    curl --create-dirs -sSLo /tmp/build-wrapper-linux.zip $URL && \
    unzip -o /tmp/build-wrapper-linux.zip -d /opt/build-wrapper-linux/ && \
    case $(uname -m) in \
        x86_64) ln -s /opt/build-wrapper-linux/build-wrapper-linux-x86/build-wrapper-linux-x86-64 /usr/local/bin/build-wrapper-linux ;; \
        aarch64) ln -s /opt/build-wrapper-linux/build-wrapper-linux-aarch64/build-wrapper-linux-aarch64 /usr/local/bin/build-wrapper-linux ;; \
    esac; \
    which build-wrapper-linux


# ==============================================================================
FROM base_python

COPY --from=SONAR_BUILDER /opt/build-wrapper-linux /opt/build-wrapper-linux/

RUN case $(uname -m) in \
        x86_64) ln -s /opt/build-wrapper-linux/build-wrapper-linux-x86/build-wrapper-linux-x86-64 /usr/local/bin/build-wrapper-linux  ;; \
        aarch64) ln ln -s /opt/build-wrapper-linux/build-wrapper-linux-aarch64/build-wrapper-linux-aarch64 /usr/local/bin/build-wrapper-linux  ;; \
    esac; \
    which build-wrapper-linux

RUN mkdir -p /.sonar/cache && \
    chmod -R 777 /.sonar/cache

ENV SONAR_SCANNER_OPTS="-server"

ARG CONAN_USER_HOME
COPY --from=conan_builder ${CONAN_USER_HOME}/.conan/ ${CONAN_USER_HOME}/.conan/
ENV CONAN_USER_HOME=${CONAN_USER_HOME}
RUN  chmod -R 777 ${CONAN_USER_HOME}

