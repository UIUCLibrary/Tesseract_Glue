ARG SONAR_SCANNER_VERSION=5.0.1.3006
ARG PYTHON_VERSION=3.11
ARG CONAN_USER_HOME=/conan
ARG PIP_FIND_LINKS=/wheels
FROM python:${PYTHON_VERSION} AS base_python
RUN apt-get update -y &&  \
    apt-get install -y --no-install-recommends ca-certificates git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache

COPY requirements/requirements-conan.txt /tmp/requirements-conan.txt
RUN python -m pip --no-cache-dir  install --upgrade pip &&  \
    pip install --no-cache-dir wheel cmake && \
    pip install --no-cache-dir setuptools && \
    pip install --no-cache-dir -r /tmp/requirements-conan.txt

FROM base_python AS wheel_builder
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
COPY requirements-dev.txt /requirements/

ARG PIP_FIND_LINKS
RUN --mount=type=cache,target=/root/.cache/pip \
    mkdir -p ${PIP_FIND_LINKS}/ &&  \
    pip wheel --wheel-dir=${PIP_FIND_LINKS}/ --cache-dir /root/.cache/pip -r /requirements/requirements-dev.txt

FROM base_python AS conan_builder
ARG CONAN_USER_HOME
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
COPY requirements/requirements-conan.txt /tmp/requirements-conan.txt
RUN pip install --no-cache-dir -r /tmp/requirements-conan.txt
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY conanfile.py /tmp/conanfile.py
RUN conan config init && \
    conan config set general.revisions_enabled=1 && \
    conan profile update settings.compiler.version=$(cc -dumpfullversion -dumpversion | grep -oE  "^([0-9]+(\.)?)([0-9]+?)") default && \
    conan install /tmp --build outdated --build=openjpeg --no-import -pr:b=default && \
    conan install /tmp --build outdated --build=openjpeg --no-import -pr:b=default -s build_type=Debug && \
    conan remove "*" -b --src -f && \
    conan remove --locks

#==============================================================================

FROM base_python AS SONAR_BUILDER
RUN apt-get update && \
    apt-get install  -y --no-install-recommends unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG SONAR_SCANNER_VERSION
ARG SONAR_SCANNER_HOME=/opt/sonar/${SONAR_SCANNER_VERSION}-linux
ENV SONAR_USER_HOME=/opt/sonar/.sonar

RUN curl --create-dirs -sSLo /tmp/sonar-scanner.zip \
        https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip && \
    unzip -o /tmp/sonar-scanner.zip -d /opt/sonar/ && \
    rm /tmp/sonar-scanner.zip && \
    mkdir -p ${SONAR_USER_HOME}/cache && \
    chmod -R 777 "${SONAR_USER_HOME}" &&\
    ln -s /opt/sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
    which sonar-scanner


RUN curl --create-dirs -sSLo /tmp/build-wrapper-linux-x86.zip https://sonarcloud.io/static/cpp/build-wrapper-linux-x86.zip && \
    unzip -o /tmp/build-wrapper-linux-x86.zip -d /opt/ && \
    ln -s /opt/build-wrapper-linux-x86/build-wrapper-linux-x86-64 /usr/local/bin/build-wrapper-linux-x86-64 && \
    which build-wrapper-linux-x86-64

# ==============================================================================
FROM base_python

RUN apt-get update &&  \
    apt-get install -y --no-install-recommends clang-tidy && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=SONAR_BUILDER /opt/sonar /opt/sonar/
COPY --from=SONAR_BUILDER /opt/build-wrapper-linux-x86 /opt/build-wrapper-linux-x86/
ARG SONAR_SCANNER_VERSION
ARG SONAR_SCANNER_HOME=/opt/sonar/${SONAR_SCANNER_VERSION}-linux
ENV SONAR_USER_HOME=/opt/sonar/.sonar

RUN ln -s /opt/sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
    which sonar-scanner

RUN ln -s /opt/build-wrapper-linux-x86/build-wrapper-linux-x86-64 /usr/local/bin/build-wrapper-linux-x86-64 && \
    which build-wrapper-linux-x86-64

RUN mkdir -p /.sonar/cache && \
    chmod -R 777 /.sonar/cache

RUN chmod -R 777 $SONAR_USER_HOME

ENV SONAR_SCANNER_OPTS="-server"

ARG PIP_FIND_LINKS
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_TRUSTED_HOST
COPY --from=wheel_builder ${PIP_FIND_LINKS}/* ${PIP_FIND_LINKS}/
COPY --from=wheel_builder requirements/ /requirements
RUN pip install --no-index --no-cache-dir --find-links=${PIP_FIND_LINKS}/ \
    -r /requirements/requirements-dev.txt

ARG CONAN_USER_HOME
COPY --from=conan_builder ${CONAN_USER_HOME}/.conan/ ${CONAN_USER_HOME}/.conan/
COPY conanfile.py /tmp/conanfile.py
ENV CONAN_USER_HOME=${CONAN_USER_HOME}

RUN conan install /tmp --build  missing --no-import && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 ${CONAN_USER_HOME}

