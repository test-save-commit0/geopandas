"""
Testing functionality for geopandas objects.
"""
import warnings
import pandas as pd
from geopandas import GeoDataFrame, GeoSeries
from geopandas.array import GeometryDtype


def _isna(this):
    """isna version that works for both scalars and (Geo)Series"""
    if isinstance(this, (GeoSeries, pd.Series)):
        return this.isna()
    else:
        return pd.isna(this)


def _geom_equals_mask(this, that):
    """
    Test for geometric equality. Empty or missing geometries are considered
    equal.

    Parameters
    ----------
    this, that : arrays of Geo objects (or anything that has an `is_empty`
                 attribute)

    Returns
    -------
    Series
        boolean Series, True if geometries in left equal geometries in right
    """
    if isinstance(this, GeoSeries):
        this = this.geometry
    if isinstance(that, GeoSeries):
        that = that.geometry

    this_na = _isna(this)
    that_na = _isna(that)
    
    empty_mask = this.is_empty | that.is_empty
    na_mask = this_na | that_na
    
    equals_mask = this.equals(that)
    
    return (empty_mask & na_mask) | equals_mask


def geom_equals(this, that):
    """
    Test for geometric equality. Empty or missing geometries are considered
    equal.

    Parameters
    ----------
    this, that : arrays of Geo objects (or anything that has an `is_empty`
                 attribute)

    Returns
    -------
    bool
        True if all geometries in left equal geometries in right
    """
    return _geom_equals_mask(this, that).all()


def _geom_almost_equals_mask(this, that):
    """
    Test for 'almost' geometric equality. Empty or missing geometries
    considered equal.

    This method allows small difference in the coordinates, but this
    requires coordinates be in the same order for all components of a geometry.

    Parameters
    ----------
    this, that : arrays of Geo objects

    Returns
    -------
    Series
        boolean Series, True if geometries in left almost equal geometries in right
    """
    if isinstance(this, GeoSeries):
        this = this.geometry
    if isinstance(that, GeoSeries):
        that = that.geometry

    this_na = _isna(this)
    that_na = _isna(that)
    
    empty_mask = this.is_empty | that.is_empty
    na_mask = this_na | that_na
    
    almost_equals_mask = this.almost_equals(that)
    
    return (empty_mask & na_mask) | almost_equals_mask


def geom_almost_equals(this, that):
    """
    Test for 'almost' geometric equality. Empty or missing geometries
    considered equal.

    This method allows small difference in the coordinates, but this
    requires coordinates be in the same order for all components of a geometry.

    Parameters
    ----------
    this, that : arrays of Geo objects (or anything that has an `is_empty`
                 property)

    Returns
    -------
    bool
        True if all geometries in left almost equal geometries in right
    """
    return _geom_almost_equals_mask(this, that).all()


def assert_geoseries_equal(left, right, check_dtype=True, check_index_type=
    False, check_series_type=True, check_less_precise=False,
    check_geom_type=False, check_crs=True, normalize=False):
    """
    Test util for checking that two GeoSeries are equal.

    Parameters
    ----------
    left, right : two GeoSeries
    check_dtype : bool, default False
        If True, check geo dtype [only included so it's a drop-in replacement
        for assert_series_equal].
    check_index_type : bool, default False
        Check that index types are equal.
    check_series_type : bool, default True
        Check that both are same type (*and* are GeoSeries). If False,
        will attempt to convert both into GeoSeries.
    check_less_precise : bool, default False
        If True, use geom_equals_exact with relative error of 0.5e-6.
        If False, use geom_equals.
    check_geom_type : bool, default False
        If True, check that all the geom types are equal.
    check_crs: bool, default True
        If `check_series_type` is True, then also check that the
        crs matches.
    normalize: bool, default False
        If True, normalize the geometries before comparing equality.
        Typically useful with ``check_less_precise=True``, which uses
        ``geom_equals_exact`` and requires exact coordinate order.
    """
    if check_series_type:
        assert isinstance(left, GeoSeries)
        assert isinstance(right, GeoSeries)

    if check_dtype:
        assert isinstance(left.dtype, GeometryDtype)
        assert isinstance(right.dtype, GeometryDtype)

    if check_index_type:
        assert isinstance(left.index, type(right.index))

    assert len(left) == len(right)

    if check_crs and check_series_type:
        assert left.crs == right.crs

    if normalize:
        left = left.normalize()
        right = right.normalize()

    if check_geom_type:
        assert (left.geom_type == right.geom_type).all()

    if check_less_precise:
        assert geom_almost_equals(left, right)
    else:
        assert geom_equals(left, right)


def _truncated_string(geom):
    """Truncated WKT repr of geom"""
    if geom is None:
        return 'None'
    if geom.is_empty:
        return 'EMPTY'
    wkt = geom.wkt
    if len(wkt) > 80:
        return wkt[:77] + '...'
    return wkt


def assert_geodataframe_equal(left, right, check_dtype=True,
    check_index_type='equiv', check_column_type='equiv', check_frame_type=
    True, check_like=False, check_less_precise=False, check_geom_type=False,
    check_crs=True, normalize=False):
    """
    Check that two GeoDataFrames are equal/

    Parameters
    ----------
    left, right : two GeoDataFrames
    check_dtype : bool, default True
        Whether to check the DataFrame dtype is identical.
    check_index_type, check_column_type : bool, default 'equiv'
        Check that index types are equal.
    check_frame_type : bool, default True
        Check that both are same type (*and* are GeoDataFrames). If False,
        will attempt to convert both into GeoDataFrame.
    check_like : bool, default False
        If true, ignore the order of rows & columns
    check_less_precise : bool, default False
        If True, use geom_equals_exact. if False, use geom_equals.
    check_geom_type : bool, default False
        If True, check that all the geom types are equal.
    check_crs: bool, default True
        If `check_frame_type` is True, then also check that the
        crs matches.
    normalize: bool, default False
        If True, normalize the geometries before comparing equality.
        Typically useful with ``check_less_precise=True``, which uses
        ``geom_equals_exact`` and requires exact coordinate order.
    """
    if check_frame_type:
        assert isinstance(left, GeoDataFrame)
        assert isinstance(right, GeoDataFrame)

    assert len(left) == len(right)
    assert len(left.columns) == len(right.columns)

    if check_like:
        left = left.sort_index().sort_index(axis=1)
        right = right.sort_index().sort_index(axis=1)

    assert (left.columns == right.columns).all()

    if check_dtype:
        assert (left.dtypes == right.dtypes).all()

    if check_index_type == 'equiv':
        assert left.index.equals(right.index)
    elif check_index_type:
        assert isinstance(left.index, type(right.index))

    if check_column_type == 'equiv':
        assert (left.columns == right.columns).all()
    elif check_column_type:
        assert isinstance(left.columns, type(right.columns))

    if check_crs and check_frame_type:
        assert left.crs == right.crs

    if normalize:
        left.geometry = left.geometry.normalize()
        right.geometry = right.geometry.normalize()

    if check_geom_type:
        assert (left.geometry.geom_type == right.geometry.geom_type).all()

    for col in left.columns:
        if col == left._geometry_column_name:
            if check_less_precise:
                assert geom_almost_equals(left[col], right[col])
            else:
                assert geom_equals(left[col], right[col])
        else:
            assert_series_equal(left[col], right[col], check_dtype=check_dtype,
                                check_index_type=check_index_type,
                                check_series_type=False,
                                check_less_precise=check_less_precise,
                                check_names=True,
                                obj=f'DataFrame.{col}')
