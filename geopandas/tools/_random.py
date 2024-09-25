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
    if rng is None:
        rng = numpy.random.default_rng()

    if geom.geom_type == 'Polygon':
        return _uniform_polygon(geom, size, rng)
    elif geom.geom_type == 'LineString':
        return _uniform_line(geom, size, rng)
    elif geom.geom_type == 'MultiPolygon':
        weights = [p.area for p in geom.geoms]
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        counts = rng.multinomial(size, weights)
        points = [_uniform_polygon(p, c, rng) for p, c in zip(geom.geoms, counts) if c > 0]
        return MultiPoint([p for subpoints in points for p in subpoints.geoms])
    elif geom.geom_type == 'MultiLineString':
        weights = [l.length for l in geom.geoms]
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        counts = rng.multinomial(size, weights)
        points = [_uniform_line(l, c, rng) for l, c in zip(geom.geoms, counts) if c > 0]
        return MultiPoint([p for subpoints in points for p in subpoints.geoms])
    else:
        warn(f"Geometry type {geom.geom_type} not supported. Returning empty MultiPoint.")
        return MultiPoint()


def _uniform_line(geom, size, generator):
    """
    Sample points from an input shapely linestring
    """
    if size == 0:
        return MultiPoint()

    total_length = geom.length
    distances = generator.random(size) * total_length
    points = [geom.interpolate(distance) for distance in distances]
    return MultiPoint(points)


def _uniform_polygon(geom, size, generator):
    """
    Sample uniformly from within a polygon using batched sampling.
    """
    if size == 0:
        return MultiPoint()

    minx, miny, maxx, maxy = geom.bounds
    points = []
    batch_size = min(1000, size * 2)  # Adjust batch size as needed

    while len(points) < size:
        x = generator.uniform(minx, maxx, batch_size)
        y = generator.uniform(miny, maxy, batch_size)
        candidates = MultiPoint(list(zip(x, y)))
        valid_points = [p for p in candidates.geoms if geom.contains(p)]
        points.extend(valid_points[:size - len(points)])

    return MultiPoint(points[:size])
