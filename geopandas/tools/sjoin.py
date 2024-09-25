import warnings
from functools import partial
from typing import Optional
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame
from geopandas._compat import PANDAS_GE_30
from geopandas.array import _check_crs, _crs_mismatch_warn


def sjoin(left_df, right_df, how='inner', predicate='intersects', lsuffix=
    'left', rsuffix='right', distance=None, on_attribute=None, **kwargs):
    """Spatial join of two GeoDataFrames.

    See the User Guide page :doc:`../../user_guide/mergingdata` for details.


    Parameters
    ----------
    left_df, right_df : GeoDataFrames
    how : string, default 'inner'
        The type of join:

        * 'left': use keys from left_df; retain only left_df geometry column
        * 'right': use keys from right_df; retain only right_df geometry column
        * 'inner': use intersection of keys from both dfs; retain only
          left_df geometry column
    predicate : string, default 'intersects'
        Binary predicate. Valid values are determined by the spatial index used.
        You can check the valid values in left_df or right_df as
        ``left_df.sindex.valid_query_predicates`` or
        ``right_df.sindex.valid_query_predicates``
        Replaces deprecated ``op`` parameter.
    lsuffix : string, default 'left'
        Suffix to apply to overlapping column names (left GeoDataFrame).
    rsuffix : string, default 'right'
        Suffix to apply to overlapping column names (right GeoDataFrame).
    distance : number or array_like, optional
        Distance(s) around each input geometry within which to query the tree
        for the 'dwithin' predicate. If array_like, must be
        one-dimesional with length equal to length of left GeoDataFrame.
        Required if ``predicate='dwithin'``.
    on_attribute : string, list or tuple
        Column name(s) to join on as an additional join restriction on top
        of the spatial predicate. These must be found in both DataFrames.
        If set, observations are joined only if the predicate applies
        and values in specified columns match.

    Examples
    --------
    >>> import geodatasets
    >>> chicago = geopandas.read_file(
    ...     geodatasets.get_path("geoda.chicago_health")
    ... )
    >>> groceries = geopandas.read_file(
    ...     geodatasets.get_path("geoda.groceries")
    ... ).to_crs(chicago.crs)

    >>> chicago.head()  # doctest: +SKIP
        ComAreaID  ...                                           geometry
    0         35  ...  POLYGON ((-87.60914 41.84469, -87.60915 41.844...
    1         36  ...  POLYGON ((-87.59215 41.81693, -87.59231 41.816...
    2         37  ...  POLYGON ((-87.62880 41.80189, -87.62879 41.801...
    3         38  ...  POLYGON ((-87.60671 41.81681, -87.60670 41.816...
    4         39  ...  POLYGON ((-87.59215 41.81693, -87.59215 41.816...
    [5 rows x 87 columns]

    >>> groceries.head()  # doctest: +SKIP
        OBJECTID     Ycoord  ...  Category                         geometry
    0        16  41.973266  ...       NaN  MULTIPOINT (-87.65661 41.97321)
    1        18  41.696367  ...       NaN  MULTIPOINT (-87.68136 41.69713)
    2        22  41.868634  ...       NaN  MULTIPOINT (-87.63918 41.86847)
    3        23  41.877590  ...       new  MULTIPOINT (-87.65495 41.87783)
    4        27  41.737696  ...       NaN  MULTIPOINT (-87.62715 41.73623)
    [5 rows x 8 columns]

    >>> groceries_w_communities = geopandas.sjoin(groceries, chicago)
    >>> groceries_w_communities.head()  # doctest: +SKIP
       OBJECTID       community                           geometry
    0        16          UPTOWN  MULTIPOINT ((-87.65661 41.97321))
    1        18     MORGAN PARK  MULTIPOINT ((-87.68136 41.69713))
    2        22  NEAR WEST SIDE  MULTIPOINT ((-87.63918 41.86847))
    3        23  NEAR WEST SIDE  MULTIPOINT ((-87.65495 41.87783))
    4        27         CHATHAM  MULTIPOINT ((-87.62715 41.73623))
    [5 rows x 95 columns]

    See also
    --------
    overlay : overlay operation resulting in a new geometry
    GeoDataFrame.sjoin : equivalent method

    Notes
    -----
    Every operation in GeoPandas is planar, i.e. the potential third
    dimension is not taken into account.
    """
    pass


def _basic_checks(left_df, right_df, how, lsuffix, rsuffix, on_attribute=None):
    """Checks the validity of join input parameters.

    `how` must be one of the valid options.
    `'index_'` concatenated with `lsuffix` or `rsuffix` must not already
    exist as columns in the left or right data frames.

    Parameters
    ------------
    left_df : GeoDataFrame
    right_df : GeoData Frame
    how : str, one of 'left', 'right', 'inner'
        join type
    lsuffix : str
        left index suffix
    rsuffix : str
        right index suffix
    on_attribute : list, default None
        list of column names to merge on along with geometry
    """
    if how not in ['left', 'right', 'inner']:
        raise ValueError("`how` must be one of 'left', 'right', or 'inner'")

    if f'index_{lsuffix}' in left_df.columns:
        raise ValueError(f"'index_{lsuffix}' column already exists in left GeoDataFrame")

    if f'index_{rsuffix}' in right_df.columns:
        raise ValueError(f"'index_{rsuffix}' column already exists in right GeoDataFrame")

    if on_attribute:
        if not isinstance(on_attribute, (list, tuple)):
            raise ValueError("`on_attribute` must be a list or tuple")
        if not set(on_attribute).issubset(left_df.columns) or not set(on_attribute).issubset(right_df.columns):
            raise ValueError("All `on_attribute` columns must exist in both GeoDataFrames")


def _geom_predicate_query(left_df, right_df, predicate, distance,
    on_attribute=None):
    """Compute geometric comparisons and get matching indices.

    Parameters
    ----------
    left_df : GeoDataFrame
    right_df : GeoDataFrame
    predicate : string
        Binary predicate to query.
    on_attribute: list, default None
        list of column names to merge on along with geometry


    Returns
    -------
    DataFrame
        DataFrame with matching indices in
        columns named `_key_left` and `_key_right`.
    """
    left_sindex = left_df.sindex
    right_geom = right_df.geometry

    if predicate == 'dwithin':
        if distance is None:
            raise ValueError("Distance must be provided for 'dwithin' predicate")
        matches = left_sindex.query(right_geom, predicate=predicate, distance=distance)
    else:
        matches = left_sindex.query(right_geom, predicate=predicate)

    left_idx, right_idx = matches

    if on_attribute:
        left_idx, right_idx = _filter_shared_attribute(left_df, right_df, left_idx, right_idx, on_attribute)

    return pd.DataFrame({'_key_left': left_idx, '_key_right': right_idx})


def _reset_index_with_suffix(df, suffix, other):
    """
    Equivalent of df.reset_index(), but with adding 'suffix' to auto-generated
    column names.
    """
    df = df.reset_index()
    if df.index.name:
        df.index.name = f"{df.index.name}_{suffix}"
    else:
        df.index.name = f"index_{suffix}"

    # Rename columns that conflict with the other DataFrame
    for col in df.columns:
        if col in other.columns:
            df = df.rename(columns={col: f"{col}_{suffix}"})

    return df


def _process_column_names_with_suffix(left: pd.Index, right: pd.Index,
    suffixes, left_df, right_df):
    """
    Add suffixes to overlapping labels (ignoring the geometry column).

    This is based on pandas' merge logic at https://github.com/pandas-dev/pandas/blob/
    a0779adb183345a8eb4be58b3ad00c223da58768/pandas/core/reshape/merge.py#L2300-L2370
    """
    to_rename = {
        'left': {},
        'right': {}
    }

    left_set = set(left) - {left_df._geometry_column_name}
    right_set = set(right) - {right_df._geometry_column_name}
    overlap = left_set.intersection(right_set)

    if not overlap:
        return to_rename

    for name in overlap:
        left_suffix, right_suffix = suffixes

        if name in left_set:
            left_name = f"{name}{left_suffix}"
            to_rename['left'][name] = left_name

        if name in right_set:
            right_name = f"{name}{right_suffix}"
            to_rename['right'][name] = right_name

    return to_rename


def _restore_index(joined, index_names, index_names_original):
    """
    Set back the the original index columns, and restoring their name as `None`
    if they didn't have a name originally.
    """
    joined = joined.set_index(index_names)
    for i, name in enumerate(index_names_original):
        if name is None:
            joined.index.names[i] = None
    return joined


def _adjust_indexers(indices, distances, original_length, how, predicate):
    """
    The left/right indexers from the query represents an inner join.
    For a left or right join, we need to adjust them to include the rows
    that would not be present in an inner join.
    """
    left_index, right_index = indices
    if how == 'inner':
        return left_index, right_index, distances

    if how == 'left':
        missing = np.setdiff1d(np.arange(original_length), left_index)
        left_index = np.concatenate([left_index, missing])
        right_index = np.concatenate([right_index, np.full(len(missing), -1)])
        if distances is not None:
            distances = np.concatenate([distances, np.full(len(missing), np.inf)])
    elif how == 'right':
        missing = np.setdiff1d(np.arange(original_length), right_index)
        right_index = np.concatenate([right_index, missing])
        left_index = np.concatenate([left_index, np.full(len(missing), -1)])
        if distances is not None:
            distances = np.concatenate([distances, np.full(len(missing), np.inf)])

    return left_index, right_index, distances


def _frame_join(left_df, right_df, indices, distances, how, lsuffix,
    rsuffix, predicate, on_attribute=None):
    """Join the GeoDataFrames at the DataFrame level.

    Parameters
    ----------
    left_df : GeoDataFrame
    right_df : GeoDataFrame
    indices : tuple of ndarray
        Indices returned by the geometric join. Tuple with with integer
        indices representing the matches from `left_df` and `right_df`
        respectively.
    distances : ndarray, optional
        Passed trough and adapted based on the indices, if needed.
    how : string
        The type of join to use on the DataFrame level.
    lsuffix : string
        Suffix to apply to overlapping column names (left GeoDataFrame).
    rsuffix : string
        Suffix to apply to overlapping column names (right GeoDataFrame).
    on_attribute: list, default None
        list of column names to merge on along with geometry


    Returns
    -------
    GeoDataFrame
        Joined GeoDataFrame.
    """
    left_index, right_index = indices

    # Prepare DataFrames for join
    left = left_df.iloc[left_index].copy()
    right = right_df.iloc[right_index].copy()

    # Add distance column if provided
    if distances is not None:
        right['_distance'] = distances

    # Rename conflicting columns
    rename_dict = _process_column_names_with_suffix(left.columns, right.columns, (lsuffix, rsuffix), left_df, right_df)
    left = left.rename(columns=rename_dict['left'])
    right = right.rename(columns=rename_dict['right'])

    # Perform join
    if how == 'left':
        joined = left.join(right, how='left', lsuffix=lsuffix, rsuffix=rsuffix)
    elif how == 'right':
        joined = right.join(left, how='left', lsuffix=rsuffix, rsuffix=lsuffix)
    else:  # inner
        joined = left.join(right, how='inner', lsuffix=lsuffix, rsuffix=rsuffix)

    # Restore original index
    if how in ('left', 'inner'):
        joined.index = left_df.index[left_index]
    else:  # right
        joined.index = right_df.index[right_index]

    # Set geometry column
    if how in ('left', 'inner'):
        joined.set_geometry(left_df._geometry_column_name, inplace=True)
    else:  # right
        joined.set_geometry(right_df._geometry_column_name, inplace=True)

    return joined


def _filter_shared_attribute(left_df, right_df, l_idx, r_idx, attribute):
    """
    Returns the indices for the left and right dataframe that share the same entry
    in the attribute column. Also returns a Boolean `shared_attribute_rows` for rows
    with the same entry.
    """
    pass


def sjoin_nearest(left_df: GeoDataFrame, right_df: GeoDataFrame, how: str=
    'inner', max_distance: Optional[float]=None, lsuffix: str='left',
    rsuffix: str='right', distance_col: Optional[str]=None, exclusive: bool
    =False) ->GeoDataFrame:
    """Spatial join of two GeoDataFrames based on the distance between their geometries.

    Results will include multiple output records for a single input record
    where there are multiple equidistant nearest or intersected neighbors.

    Distance is calculated in CRS units and can be returned using the
    `distance_col` parameter.

    See the User Guide page
    https://geopandas.readthedocs.io/en/latest/docs/user_guide/mergingdata.html
    for more details.


    Parameters
    ----------
    left_df, right_df : GeoDataFrames
    how : string, default 'inner'
        The type of join:

        * 'left': use keys from left_df; retain only left_df geometry column
        * 'right': use keys from right_df; retain only right_df geometry column
        * 'inner': use intersection of keys from both dfs; retain only
          left_df geometry column
    max_distance : float, default None
        Maximum distance within which to query for nearest geometry.
        Must be greater than 0.
        The max_distance used to search for nearest items in the tree may have a
        significant impact on performance by reducing the number of input
        geometries that are evaluated for nearest items in the tree.
    lsuffix : string, default 'left'
        Suffix to apply to overlapping column names (left GeoDataFrame).
    rsuffix : string, default 'right'
        Suffix to apply to overlapping column names (right GeoDataFrame).
    distance_col : string, default None
        If set, save the distances computed between matching geometries under a
        column of this name in the joined GeoDataFrame.
    exclusive : bool, default False
        If True, the nearest geometries that are equal to the input geometry
        will not be returned, default False.

    Examples
    --------
    >>> import geodatasets
    >>> groceries = geopandas.read_file(
    ...     geodatasets.get_path("geoda.groceries")
    ... )
    >>> chicago = geopandas.read_file(
    ...     geodatasets.get_path("geoda.chicago_health")
    ... ).to_crs(groceries.crs)

    >>> chicago.head()  # doctest: +SKIP
       ComAreaID  ...                                           geometry
    0         35  ...  POLYGON ((-87.60914 41.84469, -87.60915 41.844...
    1         36  ...  POLYGON ((-87.59215 41.81693, -87.59231 41.816...
    2         37  ...  POLYGON ((-87.62880 41.80189, -87.62879 41.801...
    3         38  ...  POLYGON ((-87.60671 41.81681, -87.60670 41.816...
    4         39  ...  POLYGON ((-87.59215 41.81693, -87.59215 41.816...
    [5 rows x 87 columns]

    >>> groceries.head()  # doctest: +SKIP
       OBJECTID     Ycoord  ...  Category                           geometry
    0        16  41.973266  ...       NaN  MULTIPOINT ((-87.65661 41.97321))
    1        18  41.696367  ...       NaN  MULTIPOINT ((-87.68136 41.69713))
    2        22  41.868634  ...       NaN  MULTIPOINT ((-87.63918 41.86847))
    3        23  41.877590  ...       new  MULTIPOINT ((-87.65495 41.87783))
    4        27  41.737696  ...       NaN  MULTIPOINT ((-87.62715 41.73623))
    [5 rows x 8 columns]

    >>> groceries_w_communities = geopandas.sjoin_nearest(groceries, chicago)
    >>> groceries_w_communities[["Chain", "community", "geometry"]].head(2)
                   Chain    community                                geometry
    0     VIET HOA PLAZA       UPTOWN   MULTIPOINT ((1168268.672 1933554.35))
    1  COUNTY FAIR FOODS  MORGAN PARK  MULTIPOINT ((1162302.618 1832900.224))


    To include the distances:

    >>> groceries_w_communities = geopandas.sjoin_nearest(groceries, chicago, distance_col="distances")
    >>> groceries_w_communities[["Chain", "community", "distances"]].head(2)
                   Chain    community  distances
    0     VIET HOA PLAZA       UPTOWN        0.0
    1  COUNTY FAIR FOODS  MORGAN PARK        0.0

    In the following example, we get multiple groceries for Uptown because all
    results are equidistant (in this case zero because they intersect).
    In fact, we get 4 results in total:

    >>> chicago_w_groceries = geopandas.sjoin_nearest(groceries, chicago, distance_col="distances", how="right")
    >>> uptown_results = chicago_w_groceries[chicago_w_groceries["community"] == "UPTOWN"]
    >>> uptown_results[["Chain", "community"]]
                Chain community
    30  VIET HOA PLAZA    UPTOWN
    30      JEWEL OSCO    UPTOWN
    30          TARGET    UPTOWN
    30       Mariano's    UPTOWN

    See also
    --------
    sjoin : binary predicate joins
    GeoDataFrame.sjoin_nearest : equivalent method

    Notes
    -----
    Since this join relies on distances, results will be inaccurate
    if your geometries are in a geographic CRS.

    Every operation in GeoPandas is planar, i.e. the potential third
    dimension is not taken into account.
    """
    pass
