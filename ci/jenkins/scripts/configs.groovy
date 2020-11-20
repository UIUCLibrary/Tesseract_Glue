def getConfigurations(){
    def CONFIGURATIONS = [
    //         "3.6" : [
    //             os: [
    //                 windows:[
    //                     agents: [
    //                         build: [
    //                             dockerfile: [
    //                                 filename: 'ci/docker/windows/build/msvc/Dockerfile',
    //                                 label: 'Windows&&Docker',
    //                                 additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
    //                             ]
    //                         ],
    //                         package: [
    //                             dockerfile: [
    //                                 filename: 'ci/docker/windows/build/msvc/Dockerfile',
    //                                 label: 'Windows&&Docker',
    //                                 additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
    //                             ]
    //                         ],
    //                         test:[
    //                             whl: [
    //                                 dockerfile: [
    //                                     filename: 'ci/docker/windows/test/msvc/Dockerfile',
    //                                     label: 'Windows&&Docker',
    //                                     additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.6-windowsservercore --build-arg CHOCOLATEY_SOURCE'
    //                                 ]
    //                             ],
    //                             sdist: [
    //                                 dockerfile: [
    //                                     filename: 'ci/docker/windows/build/msvc/Dockerfile',
    //                                     label: 'Windows&&Docker',
    //                                     additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
    //                                 ]
    //                             ]
    //                         ],
    //                         devpi: [
    //                             wheel: [
    //                                 dockerfile: [
    //                                     filename: 'ci/docker/deploy/devpi/test/windows/whl/Dockerfile',
    //                                     label: 'Windows&&Docker',
    //                                     additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.6-windowsservercore'
    //                                 ]
    //                             ],
    //                             sdist: [
    //                                 dockerfile: [
    //                                     filename: 'ci/docker/deploy/devpi/test/windows/source/Dockerfile',
    //                                     label: 'Windows&&Docker',
    //                                     additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
    //                                 ]
    //                             ]
    //                         ]
    //                     ],
    //                     devpiSelector: [
    //                         sdist: "zip",
    //                         wheel: "36m-win*.*whl",
    //                     ],
    //                     pkgRegex: [
    //                         whl: "*cp36*.whl",
    //                         sdist: "uiucprescon.ocr-*.tar.gz,"
    //                     ]
    //                 ],
    //                 linux: [
    //                     agents: [
    //                         build: [
    //                             dockerfile: [
    //                                 filename: 'ci/docker/linux/build/Dockerfile',
    //                                 label: 'linux&&docker',
    //                                 additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
    //                             ]
    //                         ],
    //                         package: [
    //                             dockerfile: [
    //                                 filename: 'ci/docker/linux/package/Dockerfile',
    //                                 label: 'linux&&docker',
    //                                 additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
    //                             ]
    //                         ],
    //                         test: [
    //                             sdist: [
    //                                 dockerfile: [
    //                                     filename: 'ci/docker/linux/build/Dockerfile',
    //                                     label: 'linux&&docker',
    //                                     additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
    //                                 ]
    //                             ],
    //                             whl: [
    //                                 dockerfile: [
    //                                     filename: 'ci/docker/linux/build/Dockerfile',
    //                                     label: 'linux&&docker',
    //                                     additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
    //                                 ]
    //                             ]
    //                         ],
    //                         devpi: [
    //                             wheel: [
    //                                 dockerfile: [
    //                                     filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
    //                                     label: 'linux&&docker',
    //                                     additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
    //                                 ]
    //                             ],
    //                             sdist: [
    //                                 dockerfile: [
    //                                     filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
    //                                     label: 'linux&&docker',
    //                                     additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
    //                                 ]
    //                             ],
    //                         ],
    //                     ],
    //                     devpiSelector: [
    //                         sdist: "zip",
    //                         wheel: "36m-manylinux*.*whl",
    //                     ],
    //                     pkgRegex: [
    //                         whl: "*cp36*.whl",
    //                         sdist: "uiucprescon.ocr-*.tar.gz,"
    //                     ]
    //                 ]
    //             ],
    //             tox_env: "py36",
    //             devpiSelector: [
    //                 sdist: "zip",
    //                 whl: "36.*whl",
    //             ],
    //             pkgRegex: [
    //                 whl: "*cp36*.whl",
    //                 sdist: "*.tar.gz"
    //             ]
    //         ],
            "3.7" : [
                os: [
                    windows: [
                        agents: [
                            build: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            package: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            test: [
                                sdist: [
                                    dockerfile: [
                                        filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                        label: 'Windows&&Docker',
                                        additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                    ]
                                ],
                                whl: [
                                    dockerfile: [
                                        filename: 'ci/docker/windows/test/msvc/Dockerfile',
                                        additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.7',
                                        label: 'windows && docker',
                                    ]
                                ]
                            ],
                            devpi: [
                                wheel: [
                                    dockerfile: [
                                        filename: 'ci/docker/deploy/devpi/test/windows/whl/Dockerfile',
                                        label: 'Windows&&Docker',
                                        additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.7'
                                    ]
                                ],
                                sdist: [
                                    dockerfile: [
                                        filename: 'ci/docker/deploy/devpi/test/windows/source/Dockerfile',
                                        label: 'Windows&&Docker',
                                        additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                    ]
                                ]
                            ]
                        ],
                        devpiSelector: [
                            sdist: "zip",
                            wheel: "37m-win*.*whl",
                        ],
                        pkgRegex: [
                            whl: "*cp37*.whl",
                            sdist: "*.tar.gz"
                        ]
                    ],
                    linux: [
                        agents: [
                            build: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            package: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/package/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            test: [
                                sdist: [
                                    dockerfile: [
                                        filename: 'ci/docker/linux/build/Dockerfile',
                                        label: 'linux&&docker',
                                        additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                    ]
                                ],
                                whl: [
                                    dockerfile: [
                                        filename: 'ci/docker/linux/build/Dockerfile',
                                        label: 'linux&&docker',
                                        additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                    ]
                                ]
                            ],
                            devpi: [
                                wheel: [
                                    dockerfile: [
                                        filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                        label: 'linux&&docker',
                                        additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                    ]
                                ],
                                sdist: [
                                    dockerfile: [
                                        filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                        label: 'linux&&docker',
                                        additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                    ]
                                ]
                            ]
                        ],
                        devpiSelector: [
                            sdist: "zip",
                            wheel: "37m-manylinux*.*whl",
                        ],
                        pkgRegex: [
                            whl: "*cp37*.whl",
                            sdist: "uiucprescon.ocr-*.tar.gz,"
                        ]
                    ],
                ],
                tox_env: "py37",
                devpiSelector: [
                    sdist: "zip",
                    whl: "37.*whl",
                ],
                pkgRegex: [
                    whl: "*cp37*.whl",
                    sdist: "*.tar.gz"
                ]
            ],
            "3.8" : [
                os: [
                    windows: [
                        agents: [
                            build: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            package: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            test: [
                                sdist: [
                                    dockerfile: [
                                        filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                        label: 'Windows&&Docker',
                                        additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                    ]
                                ],
                                whl: [
                                    dockerfile: [
                                        filename: 'ci/docker/windows/test/msvc/Dockerfile',
                                        additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.8',
                                        label: 'windows && docker',
                                    ]
                                ]
                            ],
                            devpi: [
                                wheel: [
                                    dockerfile: [
                                        filename: 'ci/docker/deploy/devpi/test/windows/whl/Dockerfile',
                                        label: 'Windows&&Docker',
                                        additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.8'
                                    ]
                                ],
                                sdist: [
                                    dockerfile: [
                                        filename: 'ci/docker/deploy/devpi/test/windows/source/Dockerfile',
                                        label: 'Windows&&Docker',
                                        additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                    ]
                                ]
                            ]

                        ],
                        devpiSelector: [
                            sdist: "zip",
                            wheel: "38-win*.*whl",
                        ],
                        pkgRegex: [
                            whl: "*cp38*.whl",
                            sdist: "uiucprescon.ocr-*.tar.gz,"
                        ]
                    ],
                    linux: [
                        agents: [
                            build: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            package: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/package/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            test: [
                                sdist: [
                                    dockerfile: [
                                        filename: 'ci/docker/linux/build/Dockerfile',
                                        label: 'linux&&docker',
                                        additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                    ]
                                ],
                                whl: [
                                    dockerfile: [
                                        filename: 'ci/docker/linux/build/Dockerfile',
                                        label: 'linux&&docker',
                                        additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                    ]
                                ]
                            ],
                            devpi: [
                                wheel: [
                                    dockerfile: [
                                        filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                        label: 'linux&&docker',
                                        additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                    ]
                                ],
                                sdist: [
                                    dockerfile: [
                                        filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                        label: 'linux&&docker',
                                        additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                    ]
                                ]
                            ]
                        ],
                        devpiSelector: [
                            sdist: "zip",
                            wheel: "38-manylinux*.*whl",
                        ],
                        pkgRegex: [
                            whl: "*cp38*.whl",
                            sdist: "uiucprescon.ocr-*.tar.gz"
                        ]
                    ]
                ],
                tox_env: "py38",
                devpiSelector: [
                    sdist: "zip",
                    wheel: "38.*whl",
                ],
                pkgRegex: [
                    whl: "*cp38*.whl",
                    sdist: "*.tar.gz"
                ]
            ],
        ]
    return CONFIGURATIONS
}
return this
