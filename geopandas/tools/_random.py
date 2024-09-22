from warnings import warn
import numpy
from shapely.geometry import MultiPoint
from geopandas.array import from_shapely, points_from_xy
from geopandas.geoseries import GeoSeries


def uniform(geom, size, rng=None):
    """

    Sample uniformly at random from a geometry.

    For polygons, this samples uniformly within the area of the polygon. For lines,
    this samples uniformly along the length of the linestring. For multi-part
    geometries, the weights of each part are selected according to their relevant
    attribute (area for Polygons, length for LineStrings), and then points are
    sampled from each part uniformly.

    Any other geometry type (e.g. Point, GeometryCollection) are ignored, and an
    empty MultiPoint geometry is returned.

    Parameters
    ----------
    geom : any shapely.geometry.BaseGeometry type
        the shape that describes the area in which to sample.

    size : integer
        an integer denoting how many points to sample

    Returns
    -------
    shapely.MultiPoint geometry containing the sampled points

    Examples
    --------
    >>> from shapely.geometry import box
    >>> square = box(0,0,1,1)
    >>> uniform(square, size=102) # doctest: +SKIP
    """
    pass


def _uniform_line(geom, size, generator):
    """
    Sample points from an input shapely linestring
    """
    pass


def _uniform_polygon(geom, size, generator):
    """
    Sample uniformly from within a polygon using batched sampling.
    """
    pass
