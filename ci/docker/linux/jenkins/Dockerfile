ARG PYTHON_VERSION=3.11
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
RUN python3 -m venv venv && \
    ./venv/bin/pip --disable-pip-version-check install uv && \
    . ./venv/bin/activate && \
    uv pip install -r /tmp/requirements-dev.txt && \
    conan config init && \
    conan config set general.revisions_enabled=1 && \
    conan profile update settings.compiler.version=$(cc -dumpfullversion -dumpversion | grep -oE  "^([0-9]+(\.)?)([0-9]+?)") default && \
    conan install /tmp --build outdated --build=openjpeg --no-import -pr:b=default && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    uv cache prune && \
    rm -rf venv

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

