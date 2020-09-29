# escape=`
ARG CERTS_GENERATOR_IMAGE=mcr.microsoft.com/dotnet/framework/sdk:4.8
ARG PYTHON_DOCKER_IMAGE_BASE=python:3.7

FROM ${CERTS_GENERATOR_IMAGE} as certsgen
RUN certutil -generateSSTFromWU roots.sst

FROM ${PYTHON_DOCKER_IMAGE_BASE} as wheel_builder
COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt c:/requirements/
ENV PIP_NO_CACHE_DIR=1
RUN python -m pip install --upgrade pip ; `
    pip install wheel ; `
    pip install --upgrade setuptools ; `
    pip wheel --wheel-dir c:/wheels/ `
        -r c:/requirements/requirements-ci.txt ; `
    pip wheel --wheel-dir c:/wheels/ `
         -r c:/requirements/requirements-extras.txt; `
    Remove-Item -Force -Recurse C:\Users\ContainerAdministrator\AppData\Local\Temp

FROM ${PYTHON_DOCKER_IMAGE_BASE}
COPY --from=certsgen c:/roots.sst roots.sst
RUN certutil -addstore -f root roots.sst ; `
    del roots.sst
COPY --from=wheel_builder c:/wheels/ c:/wheels/
ENV PIP_NO_CACHE_DIR=1
COPY ci/docker/shared/python/requirements-ci.txt c:/requirements/
RUN python -m pip install --upgrade pip ; `
    pip install wheel ; `
    pip install --no-index --find-links=c:\wheels -r c:/requirements/requirements-ci.txt
ENV PIP_FIND_LINKS=c:/wheels
