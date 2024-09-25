import pandas as pd
import numpy as np
from shapely.geometry import MultiLineString, MultiPoint, MultiPolygon, GeometryCollection
from shapely.geometry.base import BaseGeometry
from shapely.geometry.collection import MultiGeometryCollection
_multi_type_map = {'Point': MultiPoint, 'LineString': MultiLineString,
    'Polygon': MultiPolygon}


def collect(x, multi=False):
    """
    Collect single part geometries into their Multi* counterpart

    Parameters
    ----------
    x : an iterable or Series of Shapely geometries, a GeoSeries, or
        a single Shapely geometry
    multi : boolean, default False
        if True, force returned geometries to be Multi* even if they
        only have one component.

    Returns
    -------
    geometry : Shapely geometry
        A single Shapely geometry object
    """
    if isinstance(x, BaseGeometry):
        if multi and not isinstance(x, tuple(_multi_type_map.values())):
            return _multi_type_map[x.geom_type]([x])
        return x

    if isinstance(x, pd.Series):
        x = x.values

    types = list(set([geom.geom_type for geom in x]))
    if len(types) > 1:
        return MultiGeometryCollection(list(x))

    geom_type = types[0]
    if geom_type in _multi_type_map:
        multi_type = _multi_type_map[geom_type]
        if multi or len(x) > 1:
            return multi_type(list(x))
        else:
            return x[0]
    else:
        return GeometryCollection(list(x))
