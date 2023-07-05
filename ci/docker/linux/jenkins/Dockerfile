ARG SONAR_SCANNER_VERSION=4.7.0.2747
ARG PYTHON_VERSION=3.11
ARG CONAN_USER_HOME=/conan
FROM python:${PYTHON_VERSION} as base_python
RUN apt-get update -y &&  \
    apt-get install -y --no-install-recommends ca-certificates git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache

COPY requirements/requirements_conan.txt /tmp/requirements_conan.txt
RUN python -m pip --no-cache-dir  install --upgrade pip &&  \
    pip install --no-cache-dir wheel cmake && \
    pip install --no-cache-dir setuptools && \
    pip install --no-cache-dir -r /tmp/requirements_conan.txt

COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /requirements/
COPY requirements/ /requirements/requirements/

FROM base_python as wheel_builder
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
RUN pip wheel -r /requirements/requirements-ci.txt --no-cache --wheel-dir /wheels/ && \
    pip wheel -r /requirements/requirements-extras.txt --no-cache --wheel-dir /wheels/

FROM base_python as conan_builder
ARG CONAN_USER_HOME
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
RUN pip install --no-cache-dir "conan>=1.51"
ARG TARGETARCH
COPY ci/docker/linux/jenkins/conan/$TARGETARCH/profile.ini  ${CONAN_USER_HOME}/.conan/profiles/default
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY conanfile.py /tmp/conanfile.py
RUN conan config init && \
    conan config set general.revisions_enabled=1
RUN conan install /tmp --build outdated --build=openjpeg --no-import -pr:b=default && \
    conan install /tmp --build outdated --build=openjpeg --no-import -pr:b=default -s build_type=Debug && \
    conan remove "*" -b --src -f && \
    conan remove --locks

#==============================================================================

FROM base_python as SONAR_BUILDER
RUN apt-get update && \
    apt-get install  -y --no-install-recommends unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG SONAR_SCANNER_VERSION
ARG SONAR_SCANNER_HOME=/opt/sonar/${SONAR_SCANNER_VERSION}-linux
ENV SONAR_USER_HOME=/opt/sonar/.sonar

RUN curl --create-dirs -sSLo /tmp/sonar-scanner.zip \
        https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-$SONAR_SCANNER_VERSION-linux.zip && \
    unzip -o /tmp/sonar-scanner.zip -d /opt/sonar/ && \
    rm /tmp/sonar-scanner.zip && \
    mkdir -p $SONAR_USER_HOME/cache && \
    chmod -R 777 "${SONAR_USER_HOME}" &&\
    ln -s /opt/sonar/sonar-scanner-$SONAR_SCANNER_VERSION-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
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

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
COPY --from=wheel_builder /wheels/* /wheels/
ARG CONAN_USER_HOME
COPY --from=conan_builder ${CONAN_USER_HOME}/.conan/ ${CONAN_USER_HOME}/.conan/
ARG TARGETARCH
COPY ci/docker/linux/jenkins/conan/$TARGETARCH/profile.ini  ${CONAN_USER_HOME}/profiles/default
COPY conanfile.py /tmp/conanfile.py

ENV CONAN_USER_HOME=${CONAN_USER_HOME}
RUN conan config init && \
    conan config set general.revisions_enabled=1

RUN conan install /tmp --build  missing --no-import && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 ${CONAN_USER_HOME}

RUN pip install  --no-cache-dir  --no-index --find-links=/wheels/ \
         -r /requirements/requirements-ci.txt
