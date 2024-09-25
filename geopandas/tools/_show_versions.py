import importlib
import platform
import sys
from collections import OrderedDict


def _get_sys_info():
    """System information

    Returns
    -------
    sys_info : dict
        system and Python version information
    """
    return OrderedDict(
        [
            ("python", sys.version.split()[0]),
            ("python-bits", f"{sys.maxsize.bit_length() + 1}"),
            ("OS", platform.system()),
            ("OS-release", platform.release()),
            ("machine", platform.machine()),
            ("processor", platform.processor()),
            ("byteorder", sys.byteorder),
            ("LC_ALL", ".".join(platform.localeconv().get("decimal_point", ""))),
            ("LANG", os.environ.get("LANG", "None")),
        ]
    )


def _get_C_info():
    """Information on system PROJ, GDAL, GEOS
    Returns
    -------
    c_info: dict
        system PROJ information
    """
    import pyproj
    import fiona
    from shapely import geos_version_string

    return OrderedDict(
        [
            ("PROJ", pyproj.proj_version_str),
            ("GDAL", fiona.__gdal_version__),
            ("GEOS", geos_version_string),
        ]
    )


def _get_deps_info():
    """Overview of the installed version of main dependencies

    Returns
    -------
    deps_info: dict
        version information on relevant Python libraries
    """
    deps = [
        "geopandas",
        "pandas",
        "fiona",
        "numpy",
        "shapely",
        "pyproj",
        "rtree",
        "matplotlib",
    ]

    def get_version(module):
        try:
            return module.__version__
        except AttributeError:
            return module.version

    deps_info = {}

    for modname in deps:
        try:
            if modname in sys.modules:
                mod = sys.modules[modname]
            else:
                mod = importlib.import_module(modname)
            ver = get_version(mod)
            deps_info[modname] = ver
        except ImportError:
            deps_info[modname] = None

    return deps_info


def show_versions():
    """
    Print system information and installed module versions.

    Examples
    --------

    ::

        $ python -c "import geopandas; geopandas.show_versions()"
    """
    sys_info = _get_sys_info()
    c_info = _get_C_info()
    deps_info = _get_deps_info()

    print("\nSystem:")
    for k, v in sys_info.items():
        print(f"{k}: {v}")

    print("\nC dependencies:")
    for k, v in c_info.items():
        print(f"{k}: {v}")

    print("\nPython dependencies:")
    for k, v in deps_info.items():
        print(f"{k}: {v}")
