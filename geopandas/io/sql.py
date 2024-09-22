import warnings
from contextlib import contextmanager
from functools import lru_cache
import pandas as pd
import shapely
import shapely.wkb
from geopandas import GeoDataFrame


@contextmanager
def _get_conn(conn_or_engine):
    """
    Yield a connection within a transaction context.

    Engine.begin() returns a Connection with an implicit Transaction while
    Connection.begin() returns the Transaction. This helper will always return a
    Connection with an implicit (possibly nested) Transaction.

    Parameters
    ----------
    conn_or_engine : Connection or Engine
        A sqlalchemy Connection or Engine instance
    Returns
    -------
    Connection
    """
    pass


def _df_to_geodf(df, geom_col='geom', crs=None, con=None):
    """
    Transforms a pandas DataFrame into a GeoDataFrame.
    The column 'geom_col' must be a geometry column in WKB representation.
    To be used to convert df based on pd.read_sql to gdf.
    Parameters
    ----------
    df : DataFrame
        pandas DataFrame with geometry column in WKB representation.
    geom_col : string, default 'geom'
        column name to convert to shapely geometries
    crs : pyproj.CRS, optional
        CRS to use for the returned GeoDataFrame. The value can be anything accepted
        by :meth:`pyproj.CRS.from_user_input() <pyproj.crs.CRS.from_user_input>`,
        such as an authority string (eg "EPSG:4326") or a WKT string.
        If not set, tries to determine CRS from the SRID associated with the
        first geometry in the database, and assigns that to all geometries.
    con : sqlalchemy.engine.Connection or sqlalchemy.engine.Engine
        Active connection to the database to query.
    Returns
    -------
    GeoDataFrame
    """
    pass


def _read_postgis(sql, con, geom_col='geom', crs=None, index_col=None,
    coerce_float=True, parse_dates=None, params=None, chunksize=None):
    """
    Returns a GeoDataFrame corresponding to the result of the query
    string, which must contain a geometry column in WKB representation.

    It is also possible to use :meth:`~GeoDataFrame.read_file` to read from a database.
    Especially for file geodatabases like GeoPackage or SpatiaLite this can be easier.

    Parameters
    ----------
    sql : string
        SQL query to execute in selecting entries from database, or name
        of the table to read from the database.
    con : sqlalchemy.engine.Connection or sqlalchemy.engine.Engine
        Active connection to the database to query.
    geom_col : string, default 'geom'
        column name to convert to shapely geometries
    crs : dict or str, optional
        CRS to use for the returned GeoDataFrame; if not set, tries to
        determine CRS from the SRID associated with the first geometry in
        the database, and assigns that to all geometries.
    chunksize : int, default None
        If specified, return an iterator where chunksize is the number of rows to
        include in each chunk.

    See the documentation for pandas.read_sql for further explanation
    of the following parameters:
    index_col, coerce_float, parse_dates, params, chunksize

    Returns
    -------
    GeoDataFrame

    Examples
    --------
    PostGIS

    >>> from sqlalchemy import create_engine  # doctest: +SKIP
    >>> db_connection_url = "postgresql://myusername:mypassword@myhost:5432/mydatabase"
    >>> con = create_engine(db_connection_url)  # doctest: +SKIP
    >>> sql = "SELECT geom, highway FROM roads"
    >>> df = geopandas.read_postgis(sql, con)  # doctest: +SKIP

    SpatiaLite

    >>> sql = "SELECT ST_AsBinary(geom) AS geom, highway FROM roads"
    >>> df = geopandas.read_postgis(sql, con)  # doctest: +SKIP
    """
    pass


def _get_geometry_type(gdf):
    """
    Get basic geometry type of a GeoDataFrame. See more info from:
    https://geoalchemy-2.readthedocs.io/en/latest/types.html#geoalchemy2.types._GISType

    Following rules apply:
     - if geometries all share the same geometry-type,
       geometries are inserted with the given GeometryType with following types:
        - Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon,
          GeometryCollection.
        - LinearRing geometries will be converted into LineString -objects.
     - in all other cases, geometries will be inserted with type GEOMETRY:
        - a mix of Polygons and MultiPolygons in GeoSeries
        - a mix of Points and LineStrings in GeoSeries
        - geometry is of type GeometryCollection,
          such as GeometryCollection([Point, LineStrings])
     - if any of the geometries has Z-coordinate, all records will
       be written with 3D.
    """
    pass


def _get_srid_from_crs(gdf):
    """
    Get EPSG code from CRS if available. If not, return 0.
    """
    pass


def _convert_to_ewkb(gdf, geom_name, srid):
    """Convert geometries to ewkb."""
    pass


def _write_postgis(gdf, name, con, schema=None, if_exists='fail', index=
    False, index_label=None, chunksize=None, dtype=None):
    """
    Upload GeoDataFrame into PostGIS database.

    This method requires SQLAlchemy and GeoAlchemy2, and a PostgreSQL
    Python driver (e.g. psycopg2) to be installed.

    Parameters
    ----------
    name : str
        Name of the target table.
    con : sqlalchemy.engine.Connection or sqlalchemy.engine.Engine
        Active connection to the PostGIS database.
    if_exists : {'fail', 'replace', 'append'}, default 'fail'
        How to behave if the table already exists:

        - fail: Raise a ValueError.
        - replace: Drop the table before inserting new values.
        - append: Insert new values to the existing table.
    schema : string, optional
        Specify the schema. If None, use default schema: 'public'.
    index : bool, default True
        Write DataFrame index as a column.
        Uses *index_label* as the column name in the table.
    index_label : string or sequence, default None
        Column label for index column(s).
        If None is given (default) and index is True,
        then the index names are used.
    chunksize : int, optional
        Rows will be written in batches of this size at a time.
        By default, all rows will be written at once.
    dtype : dict of column name to SQL type, default None
        Specifying the datatype for columns.
        The keys should be the column names and the values
        should be the SQLAlchemy types.

    Examples
    --------

    >>> from sqlalchemy import create_engine  # doctest: +SKIP
    >>> engine = create_engine("postgresql://myusername:mypassword@myhost:5432/mydatabase";)  # doctest: +SKIP
    >>> gdf.to_postgis("my_table", engine)  # doctest: +SKIP
    """
    pass
