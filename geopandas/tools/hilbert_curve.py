import numpy as np


def _hilbert_distance(geoms, total_bounds=None, level=16):
    """
    Calculate the distance along a Hilbert curve.

    The distances are calculated for the midpoints of the geometries in the
    GeoDataFrame.

    Parameters
    ----------
    geoms : GeometryArray
    total_bounds : 4-element array
        Total bounds of geometries - array
    level : int (1 - 16), default 16
        Determines the precision of the curve (points on the curve will
        have coordinates in the range [0, 2^level - 1]).

    Returns
    -------
    np.ndarray
        Array containing distances along the Hilbert curve

    """
    if total_bounds is None:
        total_bounds = geoms.total_bounds

    bounds = geoms.bounds
    discrete_coords = _continuous_to_discrete_coords(bounds, level, total_bounds)
    
    # Calculate Hilbert distances using the discrete coordinates
    distances = np.zeros(len(geoms), dtype=np.uint64)
    for i, (x, y) in enumerate(discrete_coords):
        distances[i] = _xy2d(level, x, y)
    
    return distances


def _continuous_to_discrete_coords(bounds, level, total_bounds):
    """
    Calculates mid points & ranges of geoms and returns
    as discrete coords

    Parameters
    ----------

    bounds : Bounds of each geometry - array

    p : The number of iterations used in constructing the Hilbert curve

    total_bounds : Total bounds of geometries - array

    Returns
    -------
    Discrete two-dimensional numpy array
    Two-dimensional array Array of hilbert distances for each geom

    """
    minx, miny, maxx, maxy = total_bounds
    
    # Calculate midpoints
    mid_x = (bounds[:, 0] + bounds[:, 2]) / 2
    mid_y = (bounds[:, 1] + bounds[:, 3]) / 2
    
    # Convert to discrete coordinates
    x_discrete = _continuous_to_discrete(mid_x, (minx, maxx), 2**level)
    y_discrete = _continuous_to_discrete(mid_y, (miny, maxy), 2**level)
    
    return np.column_stack((x_discrete, y_discrete))


def _continuous_to_discrete(vals, val_range, n):
    """
    Convert a continuous one-dimensional array to discrete integer values
    based their ranges

    Parameters
    ----------
    vals : Array of continuous values

    val_range : Tuple containing range of continuous values

    n : Number of discrete values

    Returns
    -------
    One-dimensional array of discrete ints

    """
    min_val, max_val = val_range
    scaled = (vals - min_val) / (max_val - min_val)
    return np.clip((scaled * (n - 1)).astype(int), 0, n - 1)


MAX_LEVEL = 16

def _xy2d(n, x, y):
    """
    Convert (x,y) to d
    n: int
        Number of bits for x and y
    """
    d = 0
    for s in range(n):
        d += int(((x & (1 << s)) != 0) << (2*s))
        d += int(((y & (1 << s)) != 0) << (2*s + 1))
    return d
