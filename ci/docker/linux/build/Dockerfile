ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION} as base_python

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g $GROUP_ID user && \
    useradd -u $USER_ID -s /bin/sh -m -d /home/user -g user user

RUN apt update && apt install -y ninja-build

RUN python -m pip install --upgrade pip &&  \
    pip install setuptools && \
    pip install wheel cmake

ADD ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt /requirements/
FROM base_python as wheel_builder
RUN pip wheel -r /requirements/requirements-ci.txt --no-cache --wheel-dir /wheels/ && \
    pip wheel -r /requirements/requirements-extras.txt --no-cache --wheel-dir /wheels/

FROM base_python as conan_builder
ENV PIP_FIND_LINKS=/wheels
RUN pip install conan
COPY --chown=user:user ci/docker/shared/conan/remotes.json  /home/user/.conan/remotes.json
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
ENV CONAN_USER_HOME=/home/user/
USER root
RUN pip install --no-index --find-links=/wheels/ \
         -r /requirements/requirements-ci.txt

ENV SONAR_SCANNER_VERSION=4.4.0.2170
ENV SONAR_SCANNER_HOME=/home/user/.sonar/sonar-scanner-$SONAR_SCANNER_VERSION-linux
RUN curl --create-dirs -sSLo $HOME/.sonar/sonar-scanner.zip \
        https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-$SONAR_SCANNER_VERSION-linux.zip && \
    unzip -o $HOME/.sonar/sonar-scanner.zip -d $HOME/.sonar/ && \
    rm $HOME/.sonar/sonar-scanner.zip && \
    mkdir -p /home/user/.sonar/cache && \
    chown user:user /home/user/.sonar/cache
ENV PATH=$SONAR_SCANNER_HOME/bin:$PATH
ENV SONAR_SCANNER_OPTS="-server"