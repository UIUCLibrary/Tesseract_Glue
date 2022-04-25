FROM ubuntu:20.04 as wheel_builder_base
COPY ci/docker/linux/tox/apt-packages.txt /tmp/apt-packages.txt
RUN apt update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update && \
    cat /tmp/apt-packages.txt | xargs apt install -y
RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN if id $USER_ID ; then \
        echo 'Existing user id found: Creating an alias' ;\
        groupadd --non-unique --gid $GROUP_ID user ; \
        useradd  --non-unique --uid $USER_ID -s /bin/sh -m -d /home/user -g user user  ; \
    else \
        groupadd -g $GROUP_ID user ; \
        useradd  -u $USER_ID -s /bin/sh -m -d /home/user -g user user ;\
    fi


# ******************************************************************************
FROM wheel_builder_base as wheel_builder_py36

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt  /tmp/
ENV PYTHON=python3.6
RUN $PYTHON -m pip install pip --upgrade pip && \
    $PYTHON -m pip install wheel && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -r /tmp/requirements-ci.txt && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -v -r /tmp/requirements-extras.txt

# ==============================================================================
FROM wheel_builder_base as wheel_builder_py37

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /tmp/
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
ENV PYTHON=python3.9
RUN $PYTHON -m pip install pip --upgrade pip && \
    $PYTHON -m pip install wheel && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -r /tmp/requirements-ci.txt && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -v -r /tmp/requirements-extras.txt

# ==============================================================================
# ==============================================================================
FROM wheel_builder_base as wheel_builder_py310

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /tmp/
ENV PYTHON=python3.10
RUN $PYTHON -m ensurepip --upgrade && \
    $PYTHON -m pip install pip --upgrade pip && \
    $PYTHON -m pip install wheel && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -r /tmp/requirements-ci.txt && \
    $PYTHON -m pip wheel -w /wheels --no-cache-dir -v -r /tmp/requirements-extras.txt

# ==============================================================================

FROM wheel_builder_base as conan_builder
RUN pip3 install conan cmake ninja
COPY --chown=user:user ci/docker/shared/conan/remotes.json  /home/user/.conan/remotes.json
ARG TARGETARCH
COPY --chown=user:user ci/docker/linux/tox/conan/$TARGETARCH/profile.ini  /home/user/profiles/default
USER user
WORKDIR /home/user
COPY conanfile.py /tmp/conanfile.py
RUN conan config init && \
    conan config set general.revisions_enabled=1

RUN conan install /tmp --build outdated --build=openjpeg --no-import  && \
    conan remove "*" -b --src -f && \
    conan remove --locks

# ==============================================================================

FROM wheel_builder_base

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY --from=wheel_builder_py36 /wheels/* /wheels/
COPY --from=wheel_builder_py37 /wheels/* /wheels/
COPY --from=wheel_builder_py38 /wheels/* /wheels/
COPY --from=wheel_builder_py39 /wheels/* /wheels/
COPY --from=wheel_builder_py310 /wheels/* /wheels/

RUN chmod -R 777 /wheels
ENV PIP_FIND_LINKS=/wheels
RUN pip3 install tox conan cmake devpi_client build twine


COPY --from=conan_builder --chown=user:user /home/user/.conan/ /conan/.conan/
#COPY ci/docker/shared/conan/profile.ini  /conan/.conan/profiles/default
ARG TARGETARCH
COPY ci/docker/linux/tox/conan/$TARGETARCH/profile.ini  /home/user/profiles/default
COPY ci/docker/shared/conan/remotes.json  /conan/.conan/remotes.json
ADD conanfile.py /tmp/conanfile.py
ENV CONAN_USER_HOME=/conan
RUN conan config home

RUN conan config init && \
    conan config set general.revisions_enabled=1

RUN conan install /tmp --build  missing --no-import  && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 /conan


WORKDIR /src
CMD tox --workdir /tmp/tox/  -p=auto --parallel--safe-build --recreate
