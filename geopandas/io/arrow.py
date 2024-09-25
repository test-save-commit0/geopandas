import json
import warnings
from packaging.version import Version
import numpy as np
from pandas import DataFrame, Series
import shapely
import geopandas
from geopandas import GeoDataFrame
from geopandas._compat import import_optional_dependency
from geopandas.array import from_shapely, from_wkb
from .file import _expand_user
METADATA_VERSION = '1.0.0'
SUPPORTED_VERSIONS = ['0.1.0', '0.4.0', '1.0.0-beta.1', '1.0.0', '1.1.0']
GEOARROW_ENCODINGS = ['point', 'linestring', 'polygon', 'multipoint',
    'multilinestring', 'multipolygon']
SUPPORTED_ENCODINGS = ['WKB'] + GEOARROW_ENCODINGS


def _remove_id_from_member_of_ensembles(json_dict):
    """
    Older PROJ versions will not recognize IDs of datum ensemble members that
    were added in more recent PROJ database versions.

    Cf https://github.com/opengeospatial/geoparquet/discussions/110
    and https://github.com/OSGeo/PROJ/pull/3221

    Mimicking the patch to GDAL from https://github.com/OSGeo/gdal/pull/5872
    """
    if isinstance(json_dict, dict):
        if "datum" in json_dict:
            datum = json_dict["datum"]
            if isinstance(datum, dict) and "ensemble" in datum:
                ensemble = datum["ensemble"]
                if isinstance(ensemble, dict) and "members" in ensemble:
                    members = ensemble["members"]
                    if isinstance(members, list):
                        for member in members:
                            if isinstance(member, dict):
                                member.pop("id", None)
        for value in json_dict.values():
            _remove_id_from_member_of_ensembles(value)
    elif isinstance(json_dict, list):
        for item in json_dict:
            _remove_id_from_member_of_ensembles(item)


_geometry_type_names = ['Point', 'LineString', 'LineString', 'Polygon',
    'MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection']
_geometry_type_names += [(geom_type + ' Z') for geom_type in
    _geometry_type_names]


def _get_geometry_types(series):
    """
    Get unique geometry types from a GeoSeries.
    """
    return list(series.geom_type.unique())


def _create_metadata(df, schema_version=None, geometry_encoding=None,
    write_covering_bbox=False):
    """Create and encode geo metadata dict.

    Parameters
    ----------
    df : GeoDataFrame
    schema_version : {'0.1.0', '0.4.0', '1.0.0-beta.1', '1.0.0', None}
        GeoParquet specification version; if not provided will default to
        latest supported version.
    write_covering_bbox : bool, default False
        Writes the bounding box column for each row entry with column
        name 'bbox'. Writing a bbox column can be computationally
        expensive, hence is default setting is False.

    Returns
    -------
    dict
    """
    if schema_version is None:
        schema_version = SUPPORTED_VERSIONS[-1]
    
    if schema_version not in SUPPORTED_VERSIONS:
        raise ValueError(f"Unsupported schema version: {schema_version}")
    
    geometry_columns = df.select_dtypes(include=['geometry']).columns
    if len(geometry_columns) == 0:
        raise ValueError("No geometry column found in GeoDataFrame")
    
    primary_geometry = df.geometry.name
    
    metadata = {
        "version": schema_version,
        "primary_column": primary_geometry,
        "columns": {}
    }
    
    for col in geometry_columns:
        col_metadata = {
            "encoding": geometry_encoding or "WKB",
            "geometry_types": _get_geometry_types(df[col])
        }
        
        if df[col].crs:
            col_metadata["crs"] = df[col].crs.to_wkt()
        
        if write_covering_bbox:
            bounds = df[col].total_bounds
            col_metadata["bbox"] = [bounds[0], bounds[1], bounds[2], bounds[3]]
        
        metadata["columns"][col] = col_metadata
    
    return metadata


def _encode_metadata(metadata):
    """Encode metadata dict to UTF-8 JSON string

    Parameters
    ----------
    metadata : dict

    Returns
    -------
    UTF-8 encoded JSON string
    """
    pass


def _decode_metadata(metadata_str):
    """Decode a UTF-8 encoded JSON string to dict

    Parameters
    ----------
    metadata_str : string (UTF-8 encoded)

    Returns
    -------
    dict
    """
    pass


def _validate_dataframe(df):
    """Validate that the GeoDataFrame conforms to requirements for writing
    to Parquet format.

    Raises `ValueError` if the GeoDataFrame is not valid.

    copied from `pandas.io.parquet`

    Parameters
    ----------
    df : GeoDataFrame
    """
    pass


def _validate_geo_metadata(metadata):
    """Validate geo metadata.
    Must not be empty, and must contain the structure specified above.

    Raises ValueError if metadata is not valid.

    Parameters
    ----------
    metadata : dict
    """
    pass


def _geopandas_to_arrow(df, index=None, geometry_encoding='WKB',
    schema_version=None, write_covering_bbox=None):
    """
    Helper function with main, shared logic for to_parquet/to_feather.
    """
    pass


def _to_parquet(df, path, index=None, compression='snappy',
    geometry_encoding='WKB', schema_version=None, write_covering_bbox=False,
    **kwargs):
    """
    Write a GeoDataFrame to the Parquet format.

    Any geometry columns present are serialized to WKB format in the file.

    Requires 'pyarrow'.

    This is tracking version 1.0.0 of the GeoParquet specification at:
    https://github.com/opengeospatial/geoparquet. Writing older versions is
    supported using the `schema_version` keyword.

    .. versionadded:: 0.8

    Parameters
    ----------
    path : str, path object
    index : bool, default None
        If ``True``, always include the dataframe's index(es) as columns
        in the file output.
        If ``False``, the index(es) will not be written to the file.
        If ``None``, the index(ex) will be included as columns in the file
        output except `RangeIndex` which is stored as metadata only.
    compression : {'snappy', 'gzip', 'brotli', None}, default 'snappy'
        Name of the compression to use. Use ``None`` for no compression.
    geometry_encoding : {'WKB', 'geoarrow'}, default 'WKB'
        The encoding to use for the geometry columns. Defaults to "WKB"
        for maximum interoperability. Specify "geoarrow" to use one of the
        native GeoArrow-based single-geometry type encodings.
    schema_version : {'0.1.0', '0.4.0', '1.0.0', None}
        GeoParquet specification version; if not provided will default to
        latest supported version.
    write_covering_bbox : bool, default False
        Writes the bounding box column for each row entry with column
        name 'bbox'. Writing a bbox column can be computationally
        expensive, hence is default setting is False.
    **kwargs
        Additional keyword arguments passed to pyarrow.parquet.write_table().
    """
    pass


def _to_feather(df, path, index=None, compression=None, schema_version=None,
    **kwargs):
    """
    Write a GeoDataFrame to the Feather format.

    Any geometry columns present are serialized to WKB format in the file.

    Requires 'pyarrow' >= 0.17.

    This is tracking version 1.0.0 of the GeoParquet specification for
    the metadata at: https://github.com/opengeospatial/geoparquet. Writing
    older versions is supported using the `schema_version` keyword.

    .. versionadded:: 0.8

    Parameters
    ----------
    path : str, path object
    index : bool, default None
        If ``True``, always include the dataframe's index(es) as columns
        in the file output.
        If ``False``, the index(es) will not be written to the file.
        If ``None``, the index(ex) will be included as columns in the file
        output except `RangeIndex` which is stored as metadata only.
    compression : {'zstd', 'lz4', 'uncompressed'}, optional
        Name of the compression to use. Use ``"uncompressed"`` for no
        compression. By default uses LZ4 if available, otherwise uncompressed.
    schema_version : {'0.1.0', '0.4.0', '1.0.0', None}
        GeoParquet specification version for the metadata; if not provided
        will default to latest supported version.
    kwargs
        Additional keyword arguments passed to pyarrow.feather.write_feather().
    """
    pass


def _arrow_to_geopandas(table, geo_metadata=None):
    """
    Helper function with main, shared logic for read_parquet/read_feather.
    """
    pass


def _get_filesystem_path(path, filesystem=None, storage_options=None):
    """
    Get the filesystem and path for a given filesystem and path.

    If the filesystem is not None then it's just returned as is.
    """
    pass


def _ensure_arrow_fs(filesystem):
    """
    Simplified version of pyarrow.fs._ensure_filesystem. This is only needed
    below because `pyarrow.parquet.read_metadata` does not yet accept a
    filesystem keyword (https://issues.apache.org/jira/browse/ARROW-16719)
    """
    pass


def _read_parquet_schema_and_metadata(path, filesystem):
    """
    Opening the Parquet file/dataset a first time to get the schema and metadata.

    TODO: we should look into how we can reuse opened dataset for reading the
    actual data, to avoid discovering the dataset twice (problem right now is
    that the ParquetDataset interface doesn't allow passing the filters on read)

    """
    pass


def _read_parquet(path, columns=None, storage_options=None, bbox=None, **kwargs
    ):
    """
    Load a Parquet object from the file path, returning a GeoDataFrame.

    You can read a subset of columns in the file using the ``columns`` parameter.
    However, the structure of the returned GeoDataFrame will depend on which
    columns you read:

    * if no geometry columns are read, this will raise a ``ValueError`` - you
      should use the pandas `read_parquet` method instead.
    * if the primary geometry column saved to this file is not included in
      columns, the first available geometry column will be set as the geometry
      column of the returned GeoDataFrame.

    Supports versions 0.1.0, 0.4.0 and 1.0.0 of the GeoParquet
    specification at: https://github.com/opengeospatial/geoparquet

    If 'crs' key is not present in the GeoParquet metadata associated with the
    Parquet object, it will default to "OGC:CRS84" according to the specification.

    Requires 'pyarrow'.

    .. versionadded:: 0.8

    Parameters
    ----------
    path : str, path object
    columns : list-like of strings, default=None
        If not None, only these columns will be read from the file.  If
        the primary geometry column is not included, the first secondary
        geometry read from the file will be set as the geometry column
        of the returned GeoDataFrame.  If no geometry columns are present,
        a ``ValueError`` will be raised.
    storage_options : dict, optional
        Extra options that make sense for a particular storage connection, e.g. host,
        port, username, password, etc. For HTTP(S) URLs the key-value pairs are
        forwarded to urllib as header options. For other URLs (e.g. starting with
        "s3://", and "gcs://") the key-value pairs are forwarded to fsspec. Please
        see fsspec and urllib for more details.

        When no storage options are provided and a filesystem is implemented by
        both ``pyarrow.fs`` and ``fsspec`` (e.g. "s3://") then the ``pyarrow.fs``
        filesystem is preferred. Provide the instantiated fsspec filesystem using
        the ``filesystem`` keyword if you wish to use its implementation.
    bbox : tuple, optional
        Bounding box to be used to filter selection from geoparquet data. This
        is only usable if the data was saved with the bbox covering metadata.
        Input is of the tuple format (xmin, ymin, xmax, ymax).

    **kwargs
        Any additional kwargs passed to :func:`pyarrow.parquet.read_table`.

    Returns
    -------
    GeoDataFrame

    Examples
    --------
    >>> df = geopandas.read_parquet("data.parquet")  # doctest: +SKIP

    Specifying columns to read:

    >>> df = geopandas.read_parquet(
    ...     "data.parquet",
    ...     columns=["geometry", "pop_est"]
    ... )  # doctest: +SKIP
    """
    pass


def _read_feather(path, columns=None, **kwargs):
    """
    Load a Feather object from the file path, returning a GeoDataFrame.

    You can read a subset of columns in the file using the ``columns`` parameter.
    However, the structure of the returned GeoDataFrame will depend on which
    columns you read:

    * if no geometry columns are read, this will raise a ``ValueError`` - you
      should use the pandas `read_feather` method instead.
    * if the primary geometry column saved to this file is not included in
      columns, the first available geometry column will be set as the geometry
      column of the returned GeoDataFrame.

    Supports versions 0.1.0, 0.4.0 and 1.0.0 of the GeoParquet
    specification at: https://github.com/opengeospatial/geoparquet

    If 'crs' key is not present in the Feather metadata associated with the
    Parquet object, it will default to "OGC:CRS84" according to the specification.

    Requires 'pyarrow' >= 0.17.

    .. versionadded:: 0.8

    Parameters
    ----------
    path : str, path object
    columns : list-like of strings, default=None
        If not None, only these columns will be read from the file.  If
        the primary geometry column is not included, the first secondary
        geometry read from the file will be set as the geometry column
        of the returned GeoDataFrame.  If no geometry columns are present,
        a ``ValueError`` will be raised.
    **kwargs
        Any additional kwargs passed to pyarrow.feather.read_table().

    Returns
    -------
    GeoDataFrame

    Examples
    --------
    >>> df = geopandas.read_feather("data.feather")  # doctest: +SKIP

    Specifying columns to read:

    >>> df = geopandas.read_feather(
    ...     "data.feather",
    ...     columns=["geometry", "pop_est"]
    ... )  # doctest: +SKIP
    """
    pass
