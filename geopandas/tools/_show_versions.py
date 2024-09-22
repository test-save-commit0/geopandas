import importlib
import platform
import sys


def _get_sys_info():
    """System information

    Returns
    -------
    sys_info : dict
        system and Python version information
    """
    pass


def _get_C_info():
    """Information on system PROJ, GDAL, GEOS
    Returns
    -------
    c_info: dict
        system PROJ information
    """
    pass


def _get_deps_info():
    """Overview of the installed version of main dependencies

    Returns
    -------
    deps_info: dict
        version information on relevant Python libraries
    """
    pass


def show_versions():
    """
    Print system information and installed module versions.

    Examples
    --------

    ::

        $ python -c "import geopandas; geopandas.show_versions()"
    """
    pass
