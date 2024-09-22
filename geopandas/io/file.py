from __future__ import annotations
import os
import urllib.request
import warnings
from io import IOBase
from packaging.version import Version
from pathlib import Path
from urllib.parse import urlparse as parse_url
from urllib.parse import uses_netloc, uses_params, uses_relative
import numpy as np
import pandas as pd
from pandas.api.types import is_integer_dtype
import shapely
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry
from geopandas import GeoDataFrame, GeoSeries
from geopandas._compat import HAS_PYPROJ, PANDAS_GE_20
from geopandas.io.util import vsi_path
_VALID_URLS = set(uses_relative + uses_netloc + uses_params)
_VALID_URLS.discard('')
_VALID_URLS.discard('file')
fiona = None
fiona_env = None
fiona_import_error = None
FIONA_GE_19 = False
pyogrio = None
pyogrio_import_error = None
_EXTENSION_TO_DRIVER = {'.bna': 'BNA', '.dxf': 'DXF', '.csv': 'CSV', '.shp':
    'ESRI Shapefile', '.dbf': 'ESRI Shapefile', '.json': 'GeoJSON',
    '.geojson': 'GeoJSON', '.geojsonl': 'GeoJSONSeq', '.geojsons':
    'GeoJSONSeq', '.gpkg': 'GPKG', '.gml': 'GML', '.xml': 'GML', '.gpx':
    'GPX', '.gtm': 'GPSTrackMaker', '.gtz': 'GPSTrackMaker', '.tab':
    'MapInfo File', '.mif': 'MapInfo File', '.mid': 'MapInfo File', '.dgn':
    'DGN', '.fgb': 'FlatGeobuf'}


def _expand_user(path):
    """Expand paths that use ~."""
    pass


def _is_url(url):
    """Check to see if *url* has a valid protocol."""
    pass


def _read_file(filename, bbox=None, mask=None, columns=None, rows=None,
    engine=None, **kwargs):
    """
    Returns a GeoDataFrame from a file or URL.

    Parameters
    ----------
    filename : str, path object or file-like object
        Either the absolute or relative path to the file or URL to
        be opened, or any object with a read() method (such as an open file
        or StringIO)
    bbox : tuple | GeoDataFrame or GeoSeries | shapely Geometry, default None
        Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely
        geometry. With engine="fiona", CRS mis-matches are resolved if given a GeoSeries
        or GeoDataFrame. With engine="pyogrio", bbox must be in the same CRS as the
        dataset. Tuple is (minx, miny, maxx, maxy) to match the bounds property of
        shapely geometry objects. Cannot be used with mask.
    mask : dict | GeoDataFrame or GeoSeries | shapely Geometry, default None
        Filter for features that intersect with the given dict-like geojson
        geometry, GeoSeries, GeoDataFrame or shapely geometry.
        CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame.
        Cannot be used with bbox. If multiple geometries are passed, this will
        first union all geometries, which may be computationally expensive.
    columns : list, optional
        List of column names to import from the data source. Column names
        must exactly match the names in the data source. To avoid reading
        any columns (besides the geometry column), pass an empty list-like.
        By default reads all columns.
    rows : int or slice, default None
        Load in specific rows by passing an integer (first `n` rows) or a
        slice() object.
    engine : str,  "pyogrio" or "fiona"
        The underlying library that is used to read the file. Currently, the
        supported options are "pyogrio" and "fiona". Defaults to "pyogrio" if
        installed, otherwise tries "fiona". Engine can also be set globally
        with the ``geopandas.options.io_engine`` option.
    **kwargs :
        Keyword args to be passed to the engine, and can be used to write
        to multi-layer data, store data within archives (zip files), etc.
        In case of the "pyogrio" engine, the keyword arguments are passed to
        `pyogrio.write_dataframe`. In case of the "fiona" engine, the keyword
        arguments are passed to fiona.open`. For more information on possible
        keywords, type: ``import pyogrio; help(pyogrio.write_dataframe)``.


    Examples
    --------
    >>> df = geopandas.read_file("nybb.shp")  # doctest: +SKIP

    Specifying layer of GPKG:

    >>> df = geopandas.read_file("file.gpkg", layer='cities')  # doctest: +SKIP

    Reading only first 10 rows:

    >>> df = geopandas.read_file("nybb.shp", rows=10)  # doctest: +SKIP

    Reading only geometries intersecting ``mask``:

    >>> df = geopandas.read_file("nybb.shp", mask=polygon)  # doctest: +SKIP

    Reading only geometries intersecting ``bbox``:

    >>> df = geopandas.read_file("nybb.shp", bbox=(0, 0, 10, 20))  # doctest: +SKIP

    Returns
    -------
    :obj:`geopandas.GeoDataFrame` or :obj:`pandas.DataFrame` :
        If `ignore_geometry=True` a :obj:`pandas.DataFrame` will be returned.

    Notes
    -----
    The format drivers will attempt to detect the encoding of your data, but
    may fail. In this case, the proper encoding can be specified explicitly
    by using the encoding keyword parameter, e.g. ``encoding='utf-8'``.

    When specifying a URL, geopandas will check if the server supports reading
    partial data and in that case pass the URL as is to the underlying engine,
    which will then use the network file system handler of GDAL to read from
    the URL. Otherwise geopandas will download the data from the URL and pass
    all data in-memory to the underlying engine.
    If you need more control over how the URL is read, you can specify the
    GDAL virtual filesystem manually (e.g. ``/vsicurl/https://...``). See the
    GDAL documentation on filesystems for more details
    (https://gdal.org/user/virtual_file_systems.html#vsicurl-http-https-ftp-files-random-access).

    """
    pass


def _detect_driver(path):
    """
    Attempt to auto-detect driver based on the extension
    """
    pass


def _to_file(df, filename, driver=None, schema=None, index=None, mode='w',
    crs=None, engine=None, metadata=None, **kwargs):
    """
    Write this GeoDataFrame to an OGR data source

    A dictionary of supported OGR providers is available via:

    >>> import pyogrio
    >>> pyogrio.list_drivers()  # doctest: +SKIP

    Parameters
    ----------
    df : GeoDataFrame to be written
    filename : string
        File path or file handle to write to. The path may specify a
        GDAL VSI scheme.
    driver : string, default None
        The OGR format driver used to write the vector file.
        If not specified, it attempts to infer it from the file extension.
        If no extension is specified, it saves ESRI Shapefile to a folder.
    schema : dict, default None
        If specified, the schema dictionary is passed to Fiona to
        better control how the file is written. If None, GeoPandas
        will determine the schema based on each column's dtype.
        Not supported for the "pyogrio" engine.
    index : bool, default None
        If True, write index into one or more columns (for MultiIndex).
        Default None writes the index into one or more columns only if
        the index is named, is a MultiIndex, or has a non-integer data
        type. If False, no index is written.

        .. versionadded:: 0.7
            Previously the index was not written.
    mode : string, default 'w'
        The write mode, 'w' to overwrite the existing file and 'a' to append;
        when using the pyogrio engine, you can also pass ``append=True``.
        Not all drivers support appending. For the fiona engine, the drivers
        that support appending are listed in fiona.supported_drivers or
        https://github.com/Toblerity/Fiona/blob/master/fiona/drvsupport.py.
        For the pyogrio engine, you should be able to use any driver that
        is available in your installation of GDAL that supports append
        capability; see the specific driver entry at
        https://gdal.org/drivers/vector/index.html for more information.
    crs : pyproj.CRS, default None
        If specified, the CRS is passed to Fiona to
        better control how the file is written. If None, GeoPandas
        will determine the crs based on crs df attribute.
        The value can be anything accepted
        by :meth:`pyproj.CRS.from_user_input() <pyproj.crs.CRS.from_user_input>`,
        such as an authority string (eg "EPSG:4326") or a WKT string.
    engine : str,  "pyogrio" or "fiona"
        The underlying library that is used to read the file. Currently, the
        supported options are "pyogrio" and "fiona". Defaults to "pyogrio" if
        installed, otherwise tries "fiona". Engine can also be set globally
        with the ``geopandas.options.io_engine`` option.
    metadata : dict[str, str], default None
        Optional metadata to be stored in the file. Keys and values must be
        strings. Only supported for the "GPKG" driver
        (requires Fiona >= 1.9 or pyogrio >= 0.6).
    **kwargs :
        Keyword args to be passed to the engine, and can be used to write
        to multi-layer data, store data within archives (zip files), etc.
        In case of the "fiona" engine, the keyword arguments are passed to
        fiona.open`. For more information on possible keywords, type:
        ``import fiona; help(fiona.open)``. In case of the "pyogrio" engine,
        the keyword arguments are passed to `pyogrio.write_dataframe`.

    Notes
    -----
    The format drivers will attempt to detect the encoding of your data, but
    may fail. In this case, the proper encoding can be specified explicitly
    by using the encoding keyword parameter, e.g. ``encoding='utf-8'``.
    """
    pass


def _geometry_types(df):
    """
    Determine the geometry types in the GeoDataFrame for the schema.
    """
    pass


def _list_layers(filename) ->pd.DataFrame:
    """List layers available in a file.

    Provides an overview of layers available in a file or URL together with their
    geometry types. When supported by the data source, this includes both spatial and
    non-spatial layers. Non-spatial layers are indicated by the ``"geometry_type"``
    column being ``None``. GeoPandas will not read such layers but they can be read into
    a pd.DataFrame using :func:`pyogrio.read_dataframe`.

    Parameters
    ----------
    filename : str, path object or file-like object
        Either the absolute or relative path to the file or URL to
        be opened, or any object with a read() method (such as an open file
        or StringIO)

    Returns
    -------
    pandas.DataFrame
        A DataFrame with columns "name" and "geometry_type" and one row per layer.
    """
    pass
