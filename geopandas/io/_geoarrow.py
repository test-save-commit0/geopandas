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
    if not isinstance(df, GeoDataFrame):
        raise ValueError("Input must be a GeoDataFrame")

    # Handle index
    if index is None:
        index = not isinstance(df.index, pd.RangeIndex)
    
    # Convert DataFrame to Arrow table
    table = pa.Table.from_pandas(df, preserve_index=index)
    
    # Handle geometry column
    geom_col = df.geometry.name
    geom_array = df.geometry.values
    
    if geometry_encoding == 'WKB':
        wkb_array = pa.array(geom_array.to_wkb())
        field = pa.field(geom_col, pa.binary())
        table = table.set_column(table.schema.get_field_index(geom_col), field, wkb_array)
    elif geometry_encoding == 'geoarrow':
        if include_z is None:
            include_z = geom_array.has_z.any()
        
        coord_type = pa.float64()
        if interleaved:
            coords = [g.coords[:] for g in geom_array]
            if include_z:
                coords_array = pa.list_(pa.list_(coord_type, 3))
            else:
                coords_array = pa.list_(pa.list_(coord_type, 2))
            coords_array = pa.array(coords, type=coords_array)
        else:
            x, y = zip(*[(c[0], c[1]) for g in geom_array for c in g.coords])
            if include_z:
                z = [c[2] if len(c) > 2 else float('nan') for g in geom_array for c in g.coords]
                coords_array = pa.StructArray.from_arrays([pa.array(x), pa.array(y), pa.array(z)], ['x', 'y', 'z'])
            else:
                coords_array = pa.StructArray.from_arrays([pa.array(x), pa.array(y)], ['x', 'y'])
        
        geom_type = pa.array([g.geom_type for g in geom_array], pa.string())
        field = pa.field(geom_col, pa.struct([('type', pa.string()), ('coordinates', coords_array.type)]))
        geoarrow_array = pa.StructArray.from_arrays([geom_type, coords_array], ['type', 'coordinates'])
        table = table.set_column(table.schema.get_field_index(geom_col), field, geoarrow_array)
    else:
        raise ValueError("Invalid geometry_encoding. Must be 'WKB' or 'geoarrow'")
    
    return table


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
    if not isinstance(table, pa.Table):
        raise ValueError("Input must be a pyarrow.Table")

    # Convert Arrow table to pandas DataFrame
    df = table.to_pandas()

    # Find geometry column
    if geometry is None:
        geometry_columns = [field.name for field in table.schema if 
                            isinstance(field.type, pa.BinaryType) or 
                            (isinstance(field.type, pa.StructType) and 'type' in field.type.names and 'coordinates' in field.type.names)]
        if not geometry_columns:
            raise ValueError("No geometry column found in the Arrow table")
        geometry = geometry_columns[0]
    elif geometry not in table.column_names:
        raise ValueError(f"Specified geometry column '{geometry}' not found in the Arrow table")

    # Convert geometry column
    if isinstance(table.field(geometry).type, pa.BinaryType):
        # WKB encoding
        df[geometry] = from_wkb(df[geometry])
    elif isinstance(table.field(geometry).type, pa.StructType):
        # GeoArrow encoding
        geom_array = table[geometry]
        geom_type = geom_array.field('type').to_pylist()
        coords = geom_array.field('coordinates').to_pylist()
        
        geometries = []
        for gtype, coord in zip(geom_type, coords):
            if gtype == 'Point':
                geometries.append(shapely.Point(coord[0]))
            elif gtype == 'LineString':
                geometries.append(shapely.LineString(coord))
            elif gtype == 'Polygon':
                geometries.append(shapely.Polygon(coord[0], coord[1:]))
            elif gtype == 'MultiPoint':
                geometries.append(shapely.MultiPoint(coord))
            elif gtype == 'MultiLineString':
                geometries.append(shapely.MultiLineString(coord))
            elif gtype == 'MultiPolygon':
                geometries.append(shapely.MultiPolygon([shapely.Polygon(p[0], p[1:]) for p in coord]))
            else:
                raise ValueError(f"Unsupported geometry type: {gtype}")
        
        df[geometry] = from_shapely(geometries)
    else:
        raise ValueError(f"Unsupported geometry encoding for column '{geometry}'")

    return GeoDataFrame(df, geometry=geometry)


def arrow_to_geometry_array(arr):
    """
    Convert Arrow array object (representing single GeoArrow array) to a
    geopandas GeometryArray.

    Specifically for GeoSeries.from_arrow.
    """
    if isinstance(arr, pa.BinaryArray):
        # WKB encoding
        return from_wkb(arr.to_pylist())
    elif isinstance(arr, pa.StructArray):
        # GeoArrow encoding
        geom_type = arr.field('type').to_pylist()
        coords = arr.field('coordinates').to_pylist()
        
        geometries = []
        for gtype, coord in zip(geom_type, coords):
            if gtype == 'Point':
                geometries.append(shapely.Point(coord[0]))
            elif gtype == 'LineString':
                geometries.append(shapely.LineString(coord))
            elif gtype == 'Polygon':
                geometries.append(shapely.Polygon(coord[0], coord[1:]))
            elif gtype == 'MultiPoint':
                geometries.append(shapely.MultiPoint(coord))
            elif gtype == 'MultiLineString':
                geometries.append(shapely.MultiLineString(coord))
            elif gtype == 'MultiPolygon':
                geometries.append(shapely.MultiPolygon([shapely.Polygon(p[0], p[1:]) for p in coord]))
            else:
                raise ValueError(f"Unsupported geometry type: {gtype}")
        
        return from_shapely(geometries)
    else:
        raise ValueError("Unsupported Arrow array type for geometry conversion")


def construct_shapely_array(arr: pa.Array, extension_name: str):
    """
    Construct a NumPy array of shapely geometries from a pyarrow.Array
    with GeoArrow extension type.

    """
    if not isinstance(arr, pa.Array):
        raise ValueError("Input must be a pyarrow.Array")

    if extension_name not in GEOARROW_ENCODINGS:
        raise ValueError(f"Unsupported GeoArrow encoding: {extension_name}")

    geom_type = GeometryType[extension_name.upper()]
    coords = arr.field('coordinates').to_pylist()

    geometries = []
    for coord in coords:
        if geom_type == GeometryType.POINT:
            geometries.append(shapely.Point(coord))
        elif geom_type == GeometryType.LINESTRING:
            geometries.append(shapely.LineString(coord))
        elif geom_type == GeometryType.POLYGON:
            geometries.append(shapely.Polygon(coord[0], coord[1:]))
        elif geom_type == GeometryType.MULTIPOINT:
            geometries.append(shapely.MultiPoint(coord))
        elif geom_type == GeometryType.MULTILINESTRING:
            geometries.append(shapely.MultiLineString(coord))
        elif geom_type == GeometryType.MULTIPOLYGON:
            geometries.append(shapely.MultiPolygon([shapely.Polygon(p[0], p[1:]) for p in coord]))

    return np.array(geometries, dtype=object)
