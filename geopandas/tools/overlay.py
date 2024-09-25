import warnings
from functools import reduce
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame, GeoSeries
from geopandas._compat import PANDAS_GE_30
from geopandas.array import _check_crs, _crs_mismatch_warn


def _ensure_geometry_column(df):
    """
    Helper function to ensure the geometry column is called 'geometry'.
    If another column with that name exists, it will be dropped.
    """
    if 'geometry' not in df.columns:
        df.set_geometry(df.geometry.name, inplace=True)
    elif not df.geometry.name == 'geometry':
        df = df.rename(columns={df.geometry.name: 'geometry'})
        df.set_geometry('geometry', inplace=True)
    return df


def _overlay_intersection(df1, df2):
    """
    Overlay Intersection operation used in overlay function
    """
    df1 = _ensure_geometry_column(df1)
    df2 = _ensure_geometry_column(df2)
    
    intersection = df1.geometry.intersection(df2.geometry)
    intersection = GeoDataFrame(geometry=intersection)
    
    df1 = df1.drop(columns='geometry')
    df2 = df2.drop(columns='geometry')
    
    return intersection.join(df1).join(df2, rsuffix='_2')


def _overlay_difference(df1, df2):
    """
    Overlay Difference operation used in overlay function
    """
    df1 = _ensure_geometry_column(df1)
    df2 = _ensure_geometry_column(df2)
    
    difference = df1.geometry.difference(df2.geometry)
    difference = GeoDataFrame(geometry=difference)
    
    df1 = df1.drop(columns='geometry')
    
    return difference.join(df1)


def _overlay_symmetric_diff(df1, df2):
    """
    Overlay Symmetric Difference operation used in overlay function
    """
    df1 = _ensure_geometry_column(df1)
    df2 = _ensure_geometry_column(df2)
    
    symmetric_difference = df1.geometry.symmetric_difference(df2.geometry)
    symmetric_difference = GeoDataFrame(geometry=symmetric_difference)
    
    df1 = df1.drop(columns='geometry')
    df2 = df2.drop(columns='geometry')
    
    left = symmetric_difference.join(df1)
    right = symmetric_difference.join(df2, rsuffix='_2')
    
    return pd.concat([left, right])


def _overlay_union(df1, df2):
    """
    Overlay Union operation used in overlay function
    """
    df1 = _ensure_geometry_column(df1)
    df2 = _ensure_geometry_column(df2)
    
    union = df1.geometry.union(df2.geometry)
    union = GeoDataFrame(geometry=union)
    
    df1 = df1.drop(columns='geometry')
    df2 = df2.drop(columns='geometry')
    
    return union.join(df1).join(df2, rsuffix='_2')


def overlay(df1, df2, how='intersection', keep_geom_type=None, make_valid=True):
    """Perform spatial overlay between two GeoDataFrames.

    Currently only supports data GeoDataFrames with uniform geometry types,
    i.e. containing only (Multi)Polygons, or only (Multi)Points, or a
    combination of (Multi)LineString and LinearRing shapes.
    Implements several methods that are all effectively subsets of the union.

    See the User Guide page :doc:`../../user_guide/set_operations` for details.

    Parameters
    ----------
    df1 : GeoDataFrame
    df2 : GeoDataFrame
    how : string
        Method of spatial overlay: 'intersection', 'union',
        'identity', 'symmetric_difference' or 'difference'.
    keep_geom_type : bool
        If True, return only geometries of the same geometry type as df1 has,
        if False, return all resulting geometries. Default is None,
        which will set keep_geom_type to True but warn upon dropping
        geometries.
    make_valid : bool, default True
        If True, any invalid input geometries are corrected with a call to make_valid(),
        if False, a `ValueError` is raised if any input geometries are invalid.

    Returns
    -------
    df : GeoDataFrame
        GeoDataFrame with new set of polygons and attributes
        resulting from the overlay

    Examples
    --------
    >>> from shapely.geometry import Polygon
    >>> polys1 = geopandas.GeoSeries([Polygon([(0,0), (2,0), (2,2), (0,2)]),
    ...                               Polygon([(2,2), (4,2), (4,4), (2,4)])])
    >>> polys2 = geopandas.GeoSeries([Polygon([(1,1), (3,1), (3,3), (1,3)]),
    ...                               Polygon([(3,3), (5,3), (5,5), (3,5)])])
    >>> df1 = geopandas.GeoDataFrame({'geometry': polys1, 'df1_data':[1,2]})
    >>> df2 = geopandas.GeoDataFrame({'geometry': polys2, 'df2_data':[1,2]})

    >>> geopandas.overlay(df1, df2, how='union')
        df1_data  df2_data                                           geometry
    0       1.0       1.0                POLYGON ((2 2, 2 1, 1 1, 1 2, 2 2))
    1       2.0       1.0                POLYGON ((2 2, 2 3, 3 3, 3 2, 2 2))
    2       2.0       2.0                POLYGON ((4 4, 4 3, 3 3, 3 4, 4 4))
    3       1.0       NaN      POLYGON ((2 0, 0 0, 0 2, 1 2, 1 1, 2 1, 2 0))
    4       2.0       NaN  MULTIPOLYGON (((3 4, 3 3, 2 3, 2 4, 3 4)), ((4...
    5       NaN       1.0  MULTIPOLYGON (((2 3, 2 2, 1 2, 1 3, 2 3)), ((3...
    6       NaN       2.0      POLYGON ((3 5, 5 5, 5 3, 4 3, 4 4, 3 4, 3 5))

    >>> geopandas.overlay(df1, df2, how='intersection')
       df1_data  df2_data                             geometry
    0         1         1  POLYGON ((2 2, 2 1, 1 1, 1 2, 2 2))
    1         2         1  POLYGON ((2 2, 2 3, 3 3, 3 2, 2 2))
    2         2         2  POLYGON ((4 4, 4 3, 3 3, 3 4, 4 4))

    >>> geopandas.overlay(df1, df2, how='symmetric_difference')
        df1_data  df2_data                                           geometry
    0       1.0       NaN      POLYGON ((2 0, 0 0, 0 2, 1 2, 1 1, 2 1, 2 0))
    1       2.0       NaN  MULTIPOLYGON (((3 4, 3 3, 2 3, 2 4, 3 4)), ((4...
    2       NaN       1.0  MULTIPOLYGON (((2 3, 2 2, 1 2, 1 3, 2 3)), ((3...
    3       NaN       2.0      POLYGON ((3 5, 5 5, 5 3, 4 3, 4 4, 3 4, 3 5))

    >>> geopandas.overlay(df1, df2, how='difference')
                                                geometry  df1_data
    0      POLYGON ((2 0, 0 0, 0 2, 1 2, 1 1, 2 1, 2 0))         1
    1  MULTIPOLYGON (((3 4, 3 3, 2 3, 2 4, 3 4)), ((4...         2

    >>> geopandas.overlay(df1, df2, how='identity')
       df1_data  df2_data                                           geometry
    0       1.0       1.0                POLYGON ((2 2, 2 1, 1 1, 1 2, 2 2))
    1       2.0       1.0                POLYGON ((2 2, 2 3, 3 3, 3 2, 2 2))
    2       2.0       2.0                POLYGON ((4 4, 4 3, 3 3, 3 4, 4 4))
    3       1.0       NaN      POLYGON ((2 0, 0 0, 0 2, 1 2, 1 1, 2 1, 2 0))
    4       2.0       NaN  MULTIPOLYGON (((3 4, 3 3, 2 3, 2 4, 3 4)), ((4...

    See also
    --------
    sjoin : spatial join
    GeoDataFrame.overlay : equivalent method

    Notes
    -----
    Every operation in GeoPandas is planar, i.e. the potential third
    dimension is not taken into account.
    """
    if make_valid:
        df1.geometry = df1.geometry.make_valid()
        df2.geometry = df2.geometry.make_valid()
    else:
        if not df1.geometry.is_valid.all() or not df2.geometry.is_valid.all():
            raise ValueError("Invalid geometries found. Use make_valid=True to correct them.")

    df1 = _ensure_geometry_column(df1)
    df2 = _ensure_geometry_column(df2)

    if how == 'intersection':
        result = _overlay_intersection(df1, df2)
    elif how == 'union':
        result = _overlay_union(df1, df2)
    elif how == 'identity':
        result = _overlay_union(df1, df2)
        result = result[result.geometry.intersects(df1.geometry.unary_union)]
    elif how == 'symmetric_difference':
        result = _overlay_symmetric_diff(df1, df2)
    elif how == 'difference':
        result = _overlay_difference(df1, df2)
    else:
        raise ValueError("Unknown overlay operation: {0}".format(how))

    if keep_geom_type is None:
        keep_geom_type = True
        warnings.warn("Default behavior of keep_geom_type will change to False in a future version.", FutureWarning)

    if keep_geom_type:
        result = result[result.geometry.geom_type == df1.geometry.geom_type[0]]

    return result
