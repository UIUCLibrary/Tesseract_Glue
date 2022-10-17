import platform
import re
import sys


def get_compiler_name() -> str:
    groups = re.match(
        '^(GCC|Clang|MSVC|MSC)',
        platform.python_compiler()
    )
    try:
        if "Clang" in groups[1]:
            if platform.system() == "Darwin":
                return 'apple-clang'
        elif "GCC" in groups[1]:
            return 'gcc'
        elif groups[1] in ['MSVC', 'MSC']:
            return 'Visual Studio'
            # return 'msvc'
        else:
            return groups[1]
    except TypeError:
        print(
            f"python compiler = {platform.python_compiler()}",
            file=sys.stderr
        )
        raise


def get_visual_studio_version():
    import winreg
    possible_versions = [
        "8.0", "9.0", "10.0", "11.0", "12.0", "14.0", "15.0", "16.0"
    ]
    installed_versions = []
    key = "SOFTWARE\Microsoft\VisualStudio\%s"

    for v in possible_versions:
        try:
            winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key % v, 0,
                            winreg.KEY_ALL_ACCESS)
            installed_versions.append(v)
        except Exception as e:
            pass
    sorted_values = sorted(installed_versions, key=lambda value: float(value))
    print(sorted_values)
    return sorted_values[-1].split(".")[0]


def get_compiler_version():
    """
    Examples of compiler data:
        GCC 10.2.1 20210110
        GCC 9.4.0
        MSC v.1916 64 bit (AMD64)
        Clang 13.1.6 (clang-1316.0.21.2)
    """
    full_version = re.search(
        r"^(?:[A-Za-z]+ )(?:v[.])?(([0-9]+[.]?)+)",
        platform.python_compiler()
    ).groups()[0]
    if get_compiler_name() == "msvc":
        # MSVC compiler uses versions like 1916 but conan wants it as 191
        return full_version[:3]
    elif get_compiler_name() == "Visual Studio":
        return get_visual_studio_version()
    print(full_version)
    # exit(1)
    parsed_version = re.findall(
        "([0-9]+)(?:[.]?)",
        full_version
    )
    if len(parsed_version) <= 2:
        return full_version
    return f"{parsed_version[0]}.{parsed_version[1]}"

