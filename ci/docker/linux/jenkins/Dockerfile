ARG PYTHON_VERSION=3.11

ARG CONAN_CENTER_PROXY_V2_URL=https://center2.conan.io
# If you want to use a diffrent remote for Conan, such as a proxy. Set the CONAN_CENTER_PROXY_V2_URL
# Not this is only for building the image. The actual conan center proxy URL is set in the remotes.json file.

ARG PIP_CACHE_DIR=/.cache/pip
# PIP Cache directory. Change this only if you need to override the default location.

ARG UV_CACHE_DIR=/.cache/uv
# UV Cache directory. Change this only if you need to override the default location.


ARG CONAN_USER_HOME=/conan
ARG CONAN_HOME=${CONAN_USER_HOME}/.conan2

ARG _CONAN_CACHE_FILE=/tmp/conan_cache_save.tgz

FROM ghcr.io/astral-sh/uv:latest AS uv_builder

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
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ARG CONAN_HOME
COPY ci/docker/linux/jenkins/conan/profile.ini ${CONAN_HOME}/profiles/default
ARG CONAN_DOWNLOAD_CACHE=/tmp/conan_download_cache
COPY ci/docker/shared/conan/remotes.json  ${CONAN_HOME}/remotes.json
ARG CONAN_CENTER_PROXY_V2_URL
ARG UV_CACHE_DIR
ARG PIP_CACHE_DIR
COPY --from=uv_builder /uv /uvx /bin/
COPY ci/docker/shared/conan/remotes.json  /tmp/remotes.json
ENV UV_PROJECT_ENVIRONMENT=/tmp/uv/venv
ARG _CONAN_CACHE_FILE
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=cache,target=${CONAN_DOWNLOAD_CACHE} \
    --mount=type=cache,target=${CONAN_HOME},sharing=locked \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=ci/docker/linux/jenkins/conan/profile.ini,target=${CONAN_HOME}/profiles/default \
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
    uv run --only-group=conan conan install -pr:b=default --build missing /tmp -s build_type=Debug && \
    uv run --only-group=conan conan cache clean '*' --build --temp && \
    uv run --only-group=conan conan graph info /tmp/conanfile.py --lockfile=/tmp/conan.lock --format=json -c tools.graph:skip_build=True -c tools.graph:skip_test=True -s build_type=Release > graph.json && \
    uv run --only-group=conan conan graph info /tmp/conanfile.py --lockfile=/tmp/conan.lock --format=json -c tools.graph:skip_build=True -s build_type=Debug > graph-debug.json && \
    uv run --only-group=conan conan list --graph=graph.json --format=json > pkglist-release.json && \
    uv run --only-group=conan conan list --graph=graph-debug.json --format=json > pkglist-debug.json && \
    jq -s '.[0] * .[1]' pkglist-release.json pkglist-debug.json > pkglist.json && \
    uv run --only-group=conan conan cache save --file ${_CONAN_CACHE_FILE} --list pkglist.json  && \
    uv run --only-group=conan conan remove '*' --lru=1d --confirm

#==============================================================================

FROM base_python AS sonar_builder
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

COPY --from=sonar_builder /opt/build-wrapper-linux /opt/build-wrapper-linux/

RUN case $(uname -m) in \
        x86_64) ln -s /opt/build-wrapper-linux/build-wrapper-linux-x86/build-wrapper-linux-x86-64 /usr/local/bin/build-wrapper-linux  ;; \
        aarch64) ln ln -s /opt/build-wrapper-linux/build-wrapper-linux-aarch64/build-wrapper-linux-aarch64 /usr/local/bin/build-wrapper-linux  ;; \
    esac; \
    which build-wrapper-linux

RUN mkdir -p /.sonar/cache && \
    chmod -R 777 /.sonar/cache

ENV SONAR_SCANNER_OPTS="-server"

ARG CONAN_USER_HOME
ARG CONAN_HOME
ARG _CONAN_CACHE_FILE

COPY --from=uv_builder /uv /uvx /bin/
ARG UV_CACHE_DIR
COPY ci/docker/linux/jenkins/conan/profile.ini ${CONAN_HOME}/profiles/default
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=${_CONAN_CACHE_FILE},from=conan_builder,target=${_CONAN_CACHE_FILE} \
    --mount=type=bind,source=pyproject.toml,target=/tmp/uv/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/tmp/uv/uv.lock \
    --mount=type=tmpfs,target=/tmp/uv/venv \
    UV_PROJECT_ENVIRONMENT=/tmp/uv/venv UV_PROJECT=/tmp/uv uv run --only-group=conan conan cache restore ${_CONAN_CACHE_FILE} && \
    chmod -R 777 ${CONAN_HOME}
ENV CONAN_USER_HOME=${CONAN_USER_HOME} \
    CONAN_HOME=${CONAN_HOME}
