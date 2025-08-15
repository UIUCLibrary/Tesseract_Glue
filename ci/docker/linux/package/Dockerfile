ARG manylinux_image=quay.io/pypa/manylinux2014_x86_64
ARG CONAN_USER_HOME=/conan
ARG CONAN_HOME=${CONAN_USER_HOME}/.conan2

ARG CONAN_CENTER_PROXY_V2_URL=https://center2.conan.io
# If you want to use a diffrent remote for Conan, such as a proxy. Set the CONAN_CENTER_PROXY_V2_URL
# Not this is only for building the image. The actual conan center proxy URL is set in the remotes.json file.

ARG UV_CACHE_DIR=/.cache/uv
ARG PIP_CACHE_DIR=/.cache/pip
# UV Cache directory. Change this only if you need to override the default location.

FROM ${manylinux_image} AS base_python
RUN --mount=type=cache,target=/var/cache/yum \
    yum install -y lndir

# This needed to use uvx with --constraint option
RUN --mount=type=cache,target=/path/to/pipx/cache \
    pipx install "uv>=0.6.5" --force

ENV PATH=/opt/python/cp311-cp311/bin:/opt/python/cp310-cp310/bin:/opt/python/cp39-cp39/bin:/opt/python/cp38-cp38/bin:/opt/python/cp37-cp37m/bin:/opt/python/cp36-cp36m/bin:/opt/python/cp35-cp35m/bin:$PATH
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
    yum install -y perl-IPC-Cmd perl-Digest-SHA
ARG CONAN_DOWNLOAD_CACHE=/tmp/conan_download_cache
ENV UV_CONSTRAINT=/tmp/requirements-dev.txt
ARG CONAN_HOME
COPY ci/docker/shared/conan/remotes.json  ${CONAN_HOME}/remotes.json
COPY ci/docker/linux/package/conan/profile.ini ${CONAN_HOME}/profiles/default
COPY conanfile.py /tmp/conanfile.py
COPY requirements-dev.txt /tmp/requirements-dev.txt
ENV UV_CONSTRAINT=/tmp/requirements-dev.txt
ARG CONAN_CENTER_PROXY_V2_URL
ARG UV_CACHE_DIR
ARG PIP_CACHE_DIR
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=cache,target=${CONAN_DOWNLOAD_CACHE} \
    uvx --with cmake --with ninja conan profile detect --exist-ok &&  \
    cp ${CONAN_HOME}/global.conf /tmp/global.conf.original && \
    echo "core.sources:download_cache = $CONAN_DOWNLOAD_CACHE" >> ${CONAN_HOME}/global.conf && \
    if [ "$(jq -r '.remotes[0].url' ${CONAN_HOME}/remotes.json)" != "${CONAN_CENTER_PROXY_V2_URL}" ]; then \
          echo "Setting the conan center url for building cache: ${CONAN_CENTER_PROXY_V2_URL}" && \
          cp ${CONAN_HOME}/remotes.json /tmp/remotes.json && \
          uvx --with cmake --with ninja conan remote update conan-center --url ${CONAN_CENTER_PROXY_V2_URL}; \
    fi && \
    uvx --with cmake --with ninja conan install -pr:b=default --build missing /tmp  --conf=tools.cmake.cmaketoolchain:generator=Ninja && \
    uvx --with cmake --with ninja conan cache clean "*" -b --source --build --temp && \
    chmod -R 777 ${CONAN_HOME} && \
    if [ "$(jq -r '.remotes[0].url' ${CONAN_HOME}/remotes.json )" != "${CONAN_CENTER_PROXY_V2_URL}" ]; then \
      mv -f /tmp/remotes.json ${CONAN_HOME}/remotes.json; \
    fi && \
    mv -f /tmp/global.conf.original ${CONAN_HOME}/global.conf

FROM base_python
ARG CONAN_HOME
ARG CONAN_USER_HOME
ENV CONAN_USER_HOME=${CONAN_USER_HOME} \
    CONAN_HOME=${CONAN_HOME}
COPY --from=conan_builder ${CONAN_HOME}/ ${CONAN_HOME}/

