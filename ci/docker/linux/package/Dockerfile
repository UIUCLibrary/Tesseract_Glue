FROM quay.io/pypa/manylinux2014_x86_64

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


ARG CMAKE_DOWNLOAD_URL=https://github.com/Kitware/CMake/releases/download/v3.17.3/cmake-3.17.3-Linux-x86_64.sh
RUN curl -L --output  /tmp/install_cmake.sh $CMAKE_DOWNLOAD_URL && \
    chmod +x /tmp/install_cmake.sh  && \
    /tmp/install_cmake.sh  --skip-license --prefix=/usr && \
    cmake --version

ARG PYTHON_VERSION=3.8
RUN declare -A python_versions && \
    python_versions=( \
        ["3.5"]="/opt/python/cp35-cp35m" \
        ["3.6"]="/opt/python/cp36-cp36m" \
        ["3.7"]="/opt/python/cp37-cp37m" \
        ["3.8"]="/opt/python/cp38-cp38" \
        ["3.9"]="/opt/python/cp39-cp39" \
        ) && \
    if [ ${python_versions[$PYTHON_VERSION]} ] ; \
        then \
            ln -sf ${python_versions[$PYTHON_VERSION]}/bin/python /usr/bin/python ; \
            export PATH="${python_versions[$PYTHON_VERSION]}/bin:${PATH}" ; \
        else exit 1; \
    fi && \
    python -m pip install conan pep517 --no-warn-script-location && \
    ln -sf ${python_versions[$PYTHON_VERSION]}/bin/conan /usr/bin/conan
COPY conanfile.py /resources/
ENV CONAN_USER_HOME=/home/user/
RUN conan config home
RUN conan install /resources --build  missing --no-import && \
    conan remove "*" -b --src -f && \
    conan remove --locks && \
    chown -R user /home/user/.conan