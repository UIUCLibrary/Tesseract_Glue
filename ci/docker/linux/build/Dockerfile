ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION}

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g $GROUP_ID user && \
    useradd -u $USER_ID -s /bin/sh -m -d /home/user -g user user

ARG CMAKE_DOWNLOAD_URL=https://github.com/Kitware/CMake/releases/download/v3.17.3/cmake-3.17.3-Linux-x86_64.sh

RUN wget -O /tmp/install_cmake.sh $CMAKE_DOWNLOAD_URL && \
    chmod +x /tmp/install_cmake.sh  && \
     /tmp/install_cmake.sh  --skip-license

RUN apt update && apt install -y ninja-build

RUN python -m pip install --upgrade pip &&  \
    pip install setuptools && \
    pip install wheel

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


ENV SONAR_SCANNER_VERSION=4.4.0.2170
ENV SONAR_SCANNER_HOME=/home/user/.sonar/sonar-scanner-$SONAR_SCANNER_VERSION-linux
RUN curl --create-dirs -sSLo $HOME/.sonar/sonar-scanner.zip \
        https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-$SONAR_SCANNER_VERSION-linux.zip && \
    unzip -o $HOME/.sonar/sonar-scanner.zip -d $HOME/.sonar/
ENV PATH=$SONAR_SCANNER_HOME/bin:$PATH
ENV SONAR_SCANNER_OPTS="-server"
