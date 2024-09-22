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
    pass


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
    pass


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
    pass


MAX_LEVEL = 16
