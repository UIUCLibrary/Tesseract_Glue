ARG PIPX_HOME=/pipx
ARG CONAN_USER_HOME=/conan
ARG CONAN_HOME=${CONAN_USER_HOME}/.conan2
ARG PIP_CACHE_DIR=/.cache/pip
ARG PIP_INDEX_URL
ARG PIP_TRUSTED_HOST
ARG PIP_EXTRA_INDEX_URL
ARG UV_CACHE_DIR=/.cache/uv
ARG UV_INDEX_URL
ARG UV_EXTRA_INDEX_URL

ARG CONAN_CENTER_PROXY_V2_URL=https://center2.conan.io
# If you want to use a diffrent remote for Conan, such as a proxy. Set the CONAN_CENTER_PROXY_V2_URL
# Not this is only for building the image. The actual conan center proxy URL is set in the remotes.json file.

FROM ghcr.io/astral-sh/uv:latest AS uv_builder
FROM ubuntu:22.04 AS base
COPY ci/docker/linux/tox/apt-packages.txt /tmp/apt-packages.txt
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y software-properties-common gpg-agent --no-install-recommends && \
    add-apt-repository ppa:deadsnakes/ppa && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata && \
    apt-get update && \
     < /tmp/apt-packages.txt xargs apt-get install -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


FROM base AS conan_builder
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=uv_builder /uv /uvx /bin/
ARG CONAN_USER_HOME
ARG CONAN_DOWNLOAD_CACHE=/tmp/conan_download_cache
ARG CONAN_CENTER_PROXY_V2_URL
ARG UV_CACHE_DIR
ARG PIP_CACHE_DIR
ARG CONAN_HOME
COPY ci/docker/shared/conan/remotes.json  ${CONAN_HOME}/remotes.json
COPY ci/docker/linux/tox/conan/profile.ini ${CONAN_HOME}/profiles/default
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=cache,target=${CONAN_DOWNLOAD_CACHE} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=conanfile.py,target=/tmp/conanfile.py \
    --mount=type=bind,source=conan.lock,target=/tmp/conan.lock \
    uv run --only-group conan conan profile detect --exist-ok &&  \
    cp ${CONAN_HOME}/global.conf /tmp/global.conf.original && \
    echo "core.sources:download_cache = $CONAN_DOWNLOAD_CACHE" >> ${CONAN_HOME}/global.conf && \
    if [ "$(jq -r '.remotes[0].url' ${CONAN_HOME}/remotes.json )" != "${CONAN_CENTER_PROXY_V2_URL}" ]; then \
        echo "Setting the conan center url for building cache: ${CONAN_CENTER_PROXY_V2_URL}" && \
        cp ${CONAN_HOME}/remotes.json /tmp/remotes.json && \
        uv run --only-group conan conan remote update conan-center --url ${CONAN_CENTER_PROXY_V2_URL}; \
    fi && \
    uv run --only-group conan conan install /tmp -pr:b=default --build missing && \
    uv run --only-group conan conan cache clean "*" -b --source --build --temp && \
    if [ "$(jq -r '.remotes[0].url' ${CONAN_HOME}/remotes.json )" != "${CONAN_CENTER_PROXY_V2_URL}" ]; then \
      mv -f /tmp/remotes.json ${CONAN_HOME}/remotes.json; \
    fi && \
    mv -f /tmp/global.conf.original ${CONAN_HOME}/global.conf

# ==============================================================================

FROM base
ARG CONAN_USER_HOME
ARG CONAN_HOME
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ARG PIP_TRUSTED_HOST
COPY --from=uv_builder /uv /uvx /bin/
COPY --from=conan_builder --chmod=777 ${CONAN_HOME}/ ${CONAN_HOME}/


ARG PIP_CACHE_DIR
ARG UV_CACHE_DIR
RUN mkdir -p ${PIP_CACHE_DIR} && \
    chmod -R 777 ${PIP_CACHE_DIR} && \
    mkdir -p ${UV_CACHE_DIR} && \
    chmod -R 777 ${UV_CACHE_DIR}

ENV PIP_CACHE_DIR=${PIP_CACHE_DIR} \
    UV_CACHE_DIR=${UV_CACHE_DIR} \
    UV_INDEX_STRATEGY=unsafe-best-match \
    CONAN_USER_HOME=${CONAN_USER_HOME}\
    CONAN_HOME=${CONAN_HOME}
WORKDIR /src
CMD ["tox", "--workdir", "/tmp/tox/",  "-p=auto", "--parallel--safe-build", "--recreate"]
