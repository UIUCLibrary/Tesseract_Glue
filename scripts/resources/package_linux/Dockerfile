ARG manylinux_image=quay.io/pypa/manylinux2014
ARG CONAN_USER_HOME=/conan
ARG CONAN_HOME=${CONAN_USER_HOME}/.conan2

ARG CONAN_CENTER_PROXY_V2_URL=https://center2.conan.io
# If you want to use a diffrent remote for Conan, such as a proxy. Set the CONAN_CENTER_PROXY_V2_URL
# Not this is only for building the image. The actual conan center proxy URL is set in the remotes.json file.

ARG UV_CACHE_DIR=/.cache/uv
ARG PIP_CACHE_DIR=/.cache/pip
# UV Cache directory. Change this only if you need to override the default location.

ARG _CONAN_CACHE_FILE=/tmp/conan_cache_save.tgz

FROM ${manylinux_image} AS base_python
RUN --mount=type=cache,target=/var/cache/yum \
    yum install -y lndir

RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ARG CONAN_USER_HOME

FROM base_python AS conan_builder
WORKDIR /conantest
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# CentOS on ARM64 does not have a jq package, but there are binaries available via github.
# Note: I tried using the built in curl to download jq but for some reason it wasn't download a file
RUN --mount=type=cache,target=/var/cache/yum \
    case $(uname -m) in \
      x86_64)  yum install -y jq ;; \
      aarch64) yum install -y wget gawk; \
               DOWNLOAD_URL='https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-linux-arm64' && \
               EXPECTED_HASH='4dd2d8a0661df0b22f1bb9a1f9830f06b6f3b8f7d91211a1ef5d7c4f06a8b4a5' && \
               wget $DOWNLOAD_URL -P /tmp && \
               CALCULATED_HASH=$(sha256sum /tmp/jq-linux-arm64 | awk '{print $1}') && \
               if [ "$CALCULATED_HASH" != "$EXPECTED_HASH" ]; then \
                echo "Hash does not match. Expected: $EXPECTED_HASH. Got: $CALCULATED_HASH." && exit 1; \
               fi && \
               mv /tmp/jq-linux-arm64 /usr/local/bin/jq && \
               chmod +x /usr/local/bin/jq ;; \
    esac; \
    jq --version && \
    yum install -y perl-IPC-Cmd perl-Digest-SHA perl-Time-Piece
ARG CONAN_DOWNLOAD_CACHE=/tmp/conan_download_cache
ARG CONAN_HOME

COPY ci/docker/shared/conan/remotes.json  /tmp/remotes.json
ARG CONAN_CENTER_PROXY_V2_URL
ARG UV_CACHE_DIR
ARG _CONAN_CACHE_FILE
ENV UV_PROJECT_ENVIRONMENT=/tmp/uv/venv
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=cache,target=${CONAN_DOWNLOAD_CACHE} \
    --mount=type=cache,target=${CONAN_HOME},sharing=locked \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=scripts/resources/package_linux/conan/profile.ini,target=${CONAN_HOME}/profiles/default \
    --mount=type=bind,source=conanfile.py,target=/tmp/conanfile.py \
    --mount=type=bind,source=conan.lock,target=/tmp/conan.lock \
    --mount=type=tmpfs,target=${UV_PROJECT_ENVIRONMENT} \
    uv run --only-group=conan conan profile detect --exist-ok &&  \
    mv /tmp/remotes.json ${CONAN_HOME}/remotes.json && \
    cp ${CONAN_HOME}/global.conf /tmp/global.conf.original && \
    echo "core.sources:download_cache = $CONAN_DOWNLOAD_CACHE" >> ${CONAN_HOME}/global.conf && \
    if [ "$(jq -r '.remotes[0].url' ${CONAN_HOME}/remotes.json)" != "${CONAN_CENTER_PROXY_V2_URL}" ]; then \
          echo "Setting the conan center url for building cache: ${CONAN_CENTER_PROXY_V2_URL}" && \
          cp ${CONAN_HOME}/remotes.json /tmp/remotes.json && \
          uv run --only-group=conan conan remote update conan-center --url ${CONAN_CENTER_PROXY_V2_URL}; \
    fi && \
    uv run --only-group=conan conan install -pr:b=default --build missing /tmp -c tools.graph:skip_test=True -c tools.build:skip_test=True && \
    uv run --only-group=conan conan cache clean '*' --build --temp && \
    uv run --only-group=conan conan graph info /tmp/conanfile.py --lockfile=/tmp/conan.lock -c tools.graph:skip_build=True -c tools.graph:skip_test=True --format=json > graph.json && \
    uv run --only-group=conan conan list --graph=graph.json --format=json > pkglist.json && \
    uv run --only-group=conan conan cache save --file ${_CONAN_CACHE_FILE} --list pkglist.json  && \
    uv run --only-group=conan conan remove '*' --lru=1d

FROM base_python
ARG CONAN_HOME
ARG CONAN_USER_HOME
ENV CONAN_USER_HOME=${CONAN_USER_HOME} \
    CONAN_HOME=${CONAN_HOME}

COPY scripts/resources/package_linux/conan/profile.ini ${CONAN_HOME}/profiles/default
ARG _CONAN_CACHE_FILE
ARG UV_CACHE_DIR
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=${_CONAN_CACHE_FILE},from=conan_builder,target=${_CONAN_CACHE_FILE} \
    --mount=type=bind,source=pyproject.toml,target=/tmp/uv/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/tmp/uv/uv.lock \
    --mount=type=tmpfs,target=/tmp/uv/venv \
    UV_PROJECT_ENVIRONMENT=/tmp/uv/venv UV_PROJECT=/tmp/uv uv run --only-group=conan conan cache restore ${_CONAN_CACHE_FILE}

COPY scripts/resources/package_linux/make-wheel.sh /usr/local/bin/make-wheel

LABEL purpose=ci
