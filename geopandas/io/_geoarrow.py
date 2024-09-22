import json
from packaging.version import Version
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
import pyarrow as pa
from numpy.typing import NDArray
import shapely
from shapely import GeometryType
from geopandas import GeoDataFrame
from geopandas._compat import SHAPELY_GE_204
from geopandas.array import from_shapely, from_wkb
GEOARROW_ENCODINGS = ['point', 'linestring', 'polygon', 'multipoint',
    'multilinestring', 'multipolygon']


class ArrowTable:
    """
    Wrapper class for Arrow data.

    This class implements the `Arrow PyCapsule Protocol`_ (i.e. having an
    ``__arrow_c_stream__`` method). This object can then be consumed by
    your Arrow implementation of choice that supports this protocol.

    .. _Arrow PyCapsule Protocol: https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html

    Example
    -------
    >>> import pyarrow as pa
    >>> pa.table(gdf.to_arrow())  # doctest: +SKIP

    """

    def __init__(self, pa_table):
        self._pa_table = pa_table

    def __arrow_c_stream__(self, requested_schema=None):
        return self._pa_table.__arrow_c_stream__(requested_schema=
            requested_schema)


class GeoArrowArray:
    """
    Wrapper class for a geometry array as Arrow data.

    This class implements the `Arrow PyCapsule Protocol`_ (i.e. having an
    ``__arrow_c_array/stream__`` method). This object can then be consumed by
    your Arrow implementation of choice that supports this protocol.

    .. _Arrow PyCapsule Protocol: https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html

    Example
    -------
    >>> import pyarrow as pa
    >>> pa.array(ser.to_arrow())  # doctest: +SKIP

    """

    def __init__(self, pa_field, pa_array):
        self._pa_array = pa_array
        self._pa_field = pa_field

    def __arrow_c_array__(self, requested_schema=None):
        if requested_schema is not None:
            raise NotImplementedError(
                'Requested schema is not supported for geometry arrays')
        return self._pa_field.__arrow_c_schema__(
            ), self._pa_array.__arrow_c_array__()[1]


def geopandas_to_arrow(df, index=None, geometry_encoding='WKB', interleaved
    =True, include_z=None):
    """
    Convert GeoDataFrame to a pyarrow.Table.

    Parameters
    ----------
    df : GeoDataFrame
        The GeoDataFrame to convert.
    index : bool, default None
        If ``True``, always include the dataframe's index(es) as columns
        in the file output.
        If ``False``, the index(es) will not be written to the file.
        If ``None``, the index(ex) will be included as columns in the file
        output except `RangeIndex` which is stored as metadata only.
    geometry_encoding : {'WKB', 'geoarrow' }, default 'WKB'
        The GeoArrow encoding to use for the data conversion.
    interleaved : bool, default True
        Only relevant for 'geoarrow' encoding. If True, the geometries'
        coordinates are interleaved in a single fixed size list array.
        If False, the coordinates are stored as separate arrays in a
        struct type.
    include_z : bool, default None
        Only relevant for 'geoarrow' encoding (for WKB, the dimensionality
        of the individial geometries is preserved).
        If False, return 2D geometries. If True, include the third dimension
        in the output (if a geometry has no third dimension, the z-coordinates
        will be NaN). By default, will infer the dimensionality from the
        input geometries. Note that this inference can be unreliable with
        empty geometries (for a guaranteed result, it is recommended to
        specify the keyword).

    """
    pass


def arrow_to_geopandas(table, geometry=None):
    """
    Convert Arrow table object to a GeoDataFrame based on GeoArrow extension types.

    Parameters
    ----------
    table : pyarrow.Table
        The Arrow table to convert.
    geometry : str, default None
        The name of the geometry column to set as the active geometry
        column. If None, the first geometry column found will be used.

    Returns
    -------
    GeoDataFrame

    """
    pass


def arrow_to_geometry_array(arr):
    """
    Convert Arrow array object (representing single GeoArrow array) to a
    geopandas GeometryArray.

    Specifically for GeoSeries.from_arrow.
    """
    pass


def construct_shapely_array(arr: pa.Array, extension_name: str):
    """
    Construct a NumPy array of shapely geometries from a pyarrow.Array
    with GeoArrow extension type.

    """
    pass
