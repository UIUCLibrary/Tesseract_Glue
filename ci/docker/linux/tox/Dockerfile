ARG TARGETARCH=amd64
ARG COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES=9.4
ARG CONAN_USER_HOME=/conan
FROM ubuntu:20.04 as wheel_builder_base
COPY ci/docker/linux/tox/apt-packages.txt /tmp/apt-packages.txt
RUN apt update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update && \
    cat /tmp/apt-packages.txt | xargs apt install -y
RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache

# ==============================================================================
FROM wheel_builder_base as wheel_builder_py37
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /tmp/
COPY requirements /tmp/requirements

ENV PYTHON=python3.7
RUN $PYTHON -m pip install pip --upgrade pip && \
    $PYTHON -m pip install wheel && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -r /tmp/requirements-ci.txt && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -v -r /tmp/requirements-extras.txt

# ==============================================================================
FROM wheel_builder_base as wheel_builder_py38

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /tmp/
COPY requirements /tmp/requirements

ENV PYTHON=python3.8
RUN $PYTHON -m pip install pip --upgrade pip && \
    $PYTHON -m pip install wheel && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -r /tmp/requirements-ci.txt && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -v -r /tmp/requirements-extras.txt

# ==============================================================================
FROM wheel_builder_base as wheel_builder_py39

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /tmp/
COPY requirements /tmp/requirements

ENV PYTHON=python3.9
RUN $PYTHON -m pip install pip --upgrade pip && \
    $PYTHON -m pip install wheel && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -r /tmp/requirements-ci.txt && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -v -r /tmp/requirements-extras.txt

# ==============================================================================
FROM wheel_builder_base as wheel_builder_py310

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /tmp/
COPY requirements /tmp/requirements

ENV PYTHON=python3.10
RUN $PYTHON -m ensurepip --upgrade && \
    $PYTHON -m pip install pip --upgrade pip && \
    $PYTHON -m pip install wheel && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -r /tmp/requirements-ci.txt && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -v -r /tmp/requirements-extras.txt
# ==============================================================================
FROM wheel_builder_base as wheel_builder_py311

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /tmp/
COPY requirements /tmp/requirements

ENV PYTHON=python3.11
RUN $PYTHON -m ensurepip --upgrade && \
    $PYTHON -m pip install pip --upgrade pip && \
    $PYTHON -m pip install wheel && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -r /tmp/requirements-ci.txt && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -v -r /tmp/requirements-extras.txt

# ==============================================================================

FROM wheel_builder_base as conan_builder
ARG CONAN_USER_HOME
RUN pip3 install "conan>=1.53,!=1.55.0" cmake ninja
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
ARG TARGETARCH
COPY ci/docker/linux/tox/conan/$TARGETARCH/profile.ini  ${CONAN_USER_HOME}/profiles/default
COPY conanfile.py /tmp/conanfile.py
RUN conan config init && \
    conan config set general.revisions_enabled=1

COPY ci/docker/linux/tox/update_conan_compiler.py  /tmp/update_conan_compiler.py
ARG COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES
RUN python3 /tmp/update_conan_compiler.py ${CONAN_USER_HOME}/.conan/settings.yml gcc $COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES

RUN conan install /tmp --build outdated --build=openjpeg --no-import -s compiler.version=$COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES  && \
    conan remove "*" -b --src -f && \
    conan remove --locks

# ==============================================================================

FROM wheel_builder_base
ARG CONAN_USER_HOME
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY --from=wheel_builder_py37 /wheels/* /wheels/
COPY --from=wheel_builder_py38 /wheels/* /wheels/
COPY --from=wheel_builder_py39 /wheels/* /wheels/
COPY --from=wheel_builder_py310 /wheels/* /wheels/
COPY --from=wheel_builder_py311 /wheels/* /wheels/

RUN chmod -R 777 /wheels
ENV PIP_FIND_LINKS=/wheels
COPY requirements/ /tmp/requirements
RUN pip3 install -r /tmp/requirements/requirements_tox.txt "conan>=1.53,!=1.55.0" cmake "devpi-client<6.0" build twine


COPY --from=conan_builder ${CONAN_USER_HOME}/.conan/ ${CONAN_USER_HOME}/.conan/
COPY --from=conan_builder ${CONAN_USER_HOME}/.conan/settings.yml  ${CONAN_USER_HOME}/settings.yml
ARG TARGETARCH

COPY ci/docker/linux/tox/conan/$TARGETARCH/profile.ini  ${CONAN_USER_HOME}/profiles/default
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
ADD conanfile.py /tmp/conanfile.py

RUN conan config init && \
    conan config set general.revisions_enabled=1 && \
    conan profile update settings.compiler.libcxx=libstdc++11 default

ARG COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES
RUN conan install /tmp --build  missing --no-import -pr:b=default -s compiler.version=$COMPILER_VERSION_FOR_PREBUILD_CONAN_PACKAGES && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 ${CONAN_USER_HOME}

ENV CONAN_USER_HOME=${CONAN_USER_HOME}
WORKDIR /src
CMD tox --workdir /tmp/tox/  -p=auto --parallel--safe-build --recreate
