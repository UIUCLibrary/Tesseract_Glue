ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION} as base_python
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
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

RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache
#
#ENV SONAR_SCANNER_VERSION=4.6.2.2472
#ARG SONAR_SCANNER_HOME=/opt/sonar/${SONAR_SCANNER_VERSION}-linux
#ENV SONAR_USER_HOME=/opt/sonar/.sonar
#ENV SONAR_SCANNER_OPTS="-server"
#RUN curl --create-dirs -sSLo /tmp/sonar-scanner.zip \
#        https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip && \
#    unzip -o /tmp/sonar-scanner.zip -d /opt/sonar/ && \
#    rm /tmp/sonar-scanner.zip && \
#    mkdir -p $SONAR_USER_HOME/cache && \
#    chmod -R 777 "${SONAR_USER_HOME}" &&\
#    mkdir -p /home/user/.sonar/cache && \
#    chown user:user /home/user/.sonar/cache && \
#    ln -s /opt/sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
#    sonar-scanner --version
#
#RUN curl --create-dirs -sSLo /tmp/build-wrapper-linux-x86.zip https://sonarcloud.io/static/cpp/build-wrapper-linux-x86.zip && \
#    unzip -o /tmp/build-wrapper-linux-x86.zip -d /opt/ &&\
#    ln -s /opt/build-wrapper-linux-x86/build-wrapper-linux-x86-64 /usr/local/bin/build-wrapper-linux-x86-64 && \
#    which build-wrapper-linux-x86-64

RUN python -m pip install --upgrade pip &&  \
    pip install setuptools && \
    pip install wheel cmake

ADD ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /requirements/

FROM base_python as wheel_builder
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
RUN pip wheel -r /requirements/requirements-ci.txt --no-cache --wheel-dir /wheels/ && \
    pip wheel -r /requirements/requirements-extras.txt --no-cache --wheel-dir /wheels/

FROM base_python as conan_builder
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
RUN pip install conan
COPY ci/docker/linux/build/conan/profile.ini  /conan/.conan/profiles/default
COPY ci/docker/shared/conan/remotes.json  /conan/.conan/remotes.json
ENV CONAN_USER_HOME=/conan
COPY conanfile.py /tmp/conanfile.py
RUN conan config init
RUN conan install /tmp --build outdated --build=openjpeg --no-import  && \
    conan install /tmp --build outdated --build=openjpeg --no-import  -s build_type=Debug && \
    conan remove "*" -b --src -f && \
    conan remove --locks

#==============================================================================

FROM base_python as SONAR_BUILDER
RUN apt-get update && \
    apt-get install -y unzip

ENV SONAR_SCANNER_VERSION=4.6.2.2472
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

RUN apt update && apt install -y clang-tidy

COPY --from=SONAR_BUILDER /opt/sonar /opt/sonar/
COPY --from=SONAR_BUILDER /opt/build-wrapper-linux-x86 /opt/build-wrapper-linux-x86/
ENV SONAR_SCANNER_VERSION=4.6.2.2472
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

RUN pip install --no-index --find-links=/wheels/ conan
COPY --from=conan_builder /conan/.conan/ /conan/.conan/
COPY ci/docker/linux/build/conan/profile.ini  /conan/.conan/profiles/default
COPY ci/docker/shared/conan/remotes.json  /conan/.conan/remotes.json
ADD conanfile.py /tmp/conanfile.py

ENV CONAN_USER_HOME=/conan
RUN conan config init
RUN conan install /tmp --build  missing --no-import && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chmod -R 777 /conan

USER root
RUN pip install --no-index --find-links=/wheels/ \
         -r /requirements/requirements-ci.txt
