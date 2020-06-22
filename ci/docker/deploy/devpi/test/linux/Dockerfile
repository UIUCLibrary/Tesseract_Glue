ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION}

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g $GROUP_ID user && \
    useradd -u $USER_ID -s /bin/sh -m -d /home/user -g user user

ADD ci/docker/shared/python/requirements-ci.txt /requirements/

RUN pip wheel -r /requirements/requirements-ci.txt --wheel-dir /wheels/

RUN pip install --no-index --find-links=/wheels/ \
         -r /requirements/requirements-ci.txt

ENV PIP_FIND_LINKS=/wheels
USER user
WORKDIR /home/user
ADD conanfile.py /tmp/conanfile.py
ENV CONAN_USER_HOME=/home/user/
RUN conan config home
RUN conan install /tmp --build  missing --no-import