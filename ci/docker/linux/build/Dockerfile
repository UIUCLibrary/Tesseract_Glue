ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION} as base_python

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


RUN apt update && apt install -y ninja-build

RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache

ENV SONAR_SCANNER_VERSION=4.4.0.2170
ARG SONAR_SCANNER_HOME=/opt/sonar/${SONAR_SCANNER_VERSION}-linux
ENV SONAR_USER_HOME=/opt/sonar/.sonar
ENV SONAR_SCANNER_OPTS="-server"
RUN curl --create-dirs -sSLo /tmp/sonar-scanner.zip \
        https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip && \
    unzip -o /tmp/sonar-scanner.zip -d /opt/sonar/ && \
    rm /tmp/sonar-scanner.zip && \
    mkdir -p $SONAR_USER_HOME/cache && \
    chmod -R 777 "${SONAR_USER_HOME}" &&\
    mkdir -p /home/user/.sonar/cache && \
    chown user:user /home/user/.sonar/cache && \
    ln -s /opt/sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
    sonar-scanner --version


RUN python -m pip install --upgrade pip &&  \
    pip install setuptools && \
    pip install wheel cmake

ADD ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /requirements/
FROM base_python as wheel_builder
RUN pip wheel -r /requirements/requirements-ci.txt --no-cache --wheel-dir /wheels/ && \
    pip wheel -r /requirements/requirements-extras.txt --no-cache --wheel-dir /wheels/

FROM base_python as conan_builder
RUN pip install conan
COPY --chown=user:user ci/docker/shared/conan/remotes.json  /home/user/.conan/remotes.json
COPY --chown=user:user ci/docker/linux/build/conan/profile.ini  /home/user/.conan/profiles/default
USER user
WORKDIR /home/user
ADD conanfile.py /tmp/conanfile.py
ENV CONAN_USER_HOME=/home/user/
RUN conan config home
RUN conan install /tmp --build  missing --no-import  && \
    conan remove "*" -b --src -f && \
    conan remove --locks

# ==============================================================================
FROM base_python
COPY --from=wheel_builder /wheels/* /wheels/
COPY --from=conan_builder --chown=user:user /home/user/.conan/ /home/user/.conan/
COPY --chown=user:user ci/docker/linux/build/conan/profile.ini  /home/user/.conan/profiles/default
ENV CONAN_USER_HOME=/home/user/
USER root
RUN pip install --no-index --find-links=/wheels/ \
         -r /requirements/requirements-ci.txt
