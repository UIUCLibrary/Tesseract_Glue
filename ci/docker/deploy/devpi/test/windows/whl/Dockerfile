# escape=`
ARG PYTHON_DOCKER_IMAGE_BASE=python:3.7
FROM ${PYTHON_DOCKER_IMAGE_BASE}
RUN certutil -generateSSTFromWU roots.sst ; `
    certutil -addstore -f root roots.sst ; `
    del roots.sst

RUN python -m pip install --upgrade pip ; `
    pip install wheel; `
    pip install setuptools --upgrade

ADD ci/docker/shared/python/requirements-ci.txt c:/requirements/

RUN python -m pip wheel --wheel-dir=c:\wheels `
    -r c:/requirements/requirements-ci.txt

RUN pip install --no-index --find-links c:\wheels\ `
    -r c:/requirements/requirements-ci.txt

ENV PIP_FIND_LINKS=c:\wheels\
