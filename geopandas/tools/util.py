import pandas as pd
from shapely.geometry import MultiLineString, MultiPoint, MultiPolygon
from shapely.geometry.base import BaseGeometry
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

    """
    pass
