"""Tests for the clip module."""
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import GeometryCollection, LinearRing, LineString, MultiPoint, Point, Polygon, box
import geopandas
from geopandas import GeoDataFrame, GeoSeries, clip
from geopandas._compat import HAS_PYPROJ
from geopandas.tools.clip import _mask_is_list_like_rectangle
import pytest
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal
from pandas.testing import assert_index_equal
mask_variants_single_rectangle = ['single_rectangle_gdf',
    'single_rectangle_gdf_list_bounds', 'single_rectangle_gdf_tuple_bounds',
    'single_rectangle_gdf_array_bounds']
mask_variants_large_rectangle = ['larger_single_rectangle_gdf',
    'larger_single_rectangle_gdf_bounds']


@pytest.fixture
def point_gdf():
    """Create a point GeoDataFrame."""
    return GeoDataFrame(
        {'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)]},
        crs="EPSG:4326"
    )


@pytest.fixture
def point_gdf2():
    """Create a point GeoDataFrame."""
    return GeoDataFrame(
        {'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)],
         'value': [1, 2, 3]},
        crs="EPSG:4326"
    )


@pytest.fixture
def pointsoutside_nooverlap_gdf():
    """Create a point GeoDataFrame. Its points are all outside the single
    rectangle, and its bounds are outside the single rectangle's."""
    return GeoDataFrame(
        {'geometry': [Point(-1, -1), Point(-2, -2), Point(-3, -3)]},
        crs="EPSG:4326"
    )


@pytest.fixture
def pointsoutside_overlap_gdf():
    """Create a point GeoDataFrame. Its points are all outside the single
    rectangle, and its bounds are overlapping the single rectangle's."""
    return GeoDataFrame(
        {'geometry': [Point(-1, -1), Point(3, 3), Point(5, 5)]},
        crs="EPSG:4326"
    )


@pytest.fixture
def single_rectangle_gdf():
    """Create a single rectangle for clipping."""
    return GeoDataFrame(
        {'geometry': [box(0, 0, 2, 2)]},
        crs="EPSG:4326"
    )


@pytest.fixture
def single_rectangle_gdf_tuple_bounds(single_rectangle_gdf):
    """Bounds of the created single rectangle"""
    return tuple(single_rectangle_gdf.total_bounds)


@pytest.fixture
def single_rectangle_gdf_list_bounds(single_rectangle_gdf):
    """Bounds of the created single rectangle"""
    return list(single_rectangle_gdf.total_bounds)


@pytest.fixture
def single_rectangle_gdf_array_bounds(single_rectangle_gdf):
    """Bounds of the created single rectangle"""
    return single_rectangle_gdf.total_bounds


@pytest.fixture
def larger_single_rectangle_gdf():
    """Create a slightly larger rectangle for clipping.
    The smaller single rectangle is used to test the edge case where slivers
    are returned when you clip polygons. This fixture is larger which
    eliminates the slivers in the clip return.
    """
    return GeoDataFrame(
        {'geometry': [box(-1, -1, 3, 3)]},
        crs="EPSG:4326"
    )


@pytest.fixture
def larger_single_rectangle_gdf_bounds(larger_single_rectangle_gdf):
    """Bounds of the created single rectangle"""
    return larger_single_rectangle_gdf.total_bounds


@pytest.fixture
def buffered_locations(point_gdf):
    """Buffer points to create a multi-polygon."""
    return GeoDataFrame(geometry=point_gdf.geometry.buffer(1), crs=point_gdf.crs)


@pytest.fixture
def donut_geometry(buffered_locations, single_rectangle_gdf):
    """Make a geometry with a hole in the middle (a donut)."""
    return buffered_locations.geometry.unary_union.difference(single_rectangle_gdf.geometry.unary_union)


@pytest.fixture
def two_line_gdf():
    """Create Line Objects For Testing"""
    return GeoDataFrame(
        {'geometry': [LineString([(0, 0), (2, 2)]), LineString([(2, 0), (0, 2)])]},
        crs="EPSG:4326"
    )


@pytest.fixture
def multi_poly_gdf(donut_geometry):
    """Create a multi-polygon GeoDataFrame."""
    return GeoDataFrame(
        {'geometry': [donut_geometry]},
        crs="EPSG:4326"
    )


@pytest.fixture
def multi_line(two_line_gdf):
    """Create a multi-line GeoDataFrame.
    This GDF has one multiline and one regular line."""
    multi = two_line_gdf.geometry.unary_union
    return GeoDataFrame(
        {'geometry': [multi, two_line_gdf.geometry.iloc[0]]},
        crs="EPSG:4326"
    )


@pytest.fixture
def multi_point(point_gdf):
    """Create a multi-point GeoDataFrame."""
    multi = MultiPoint(point_gdf.geometry.tolist())
    return GeoDataFrame(
        {'geometry': [multi]},
        crs="EPSG:4326"
    )


@pytest.fixture
def mixed_gdf():
    """Create a Mixed Polygon and LineString For Testing"""
    return GeoDataFrame(
        {'geometry': [Polygon([(0, 0), (1, 1), (0, 1)]), LineString([(0, 0), (1, 1)])]},
        crs="EPSG:4326"
    )


@pytest.fixture
def geomcol_gdf():
    """Create a Mixed Polygon and LineString For Testing"""
    return GeoDataFrame(
        {'geometry': [GeometryCollection([Polygon([(0, 0), (1, 1), (0, 1)]), LineString([(0, 0), (1, 1)])])]},
        crs="EPSG:4326"
    )


@pytest.fixture
def sliver_line():
    """Create a line that will create a point when clipped."""
    return GeoDataFrame(
        {'geometry': [LineString([(0, 0), (2, 2)])]},
        crs="EPSG:4326"
    )


def test_not_gdf(single_rectangle_gdf):
    """Non-GeoDataFrame inputs raise attribute errors."""
    with pytest.raises(AttributeError):
        clip(np.array([1, 2, 3]), single_rectangle_gdf)


def test_non_overlapping_geoms():
    """Test that a bounding box returns empty if the extents don't overlap"""
    points = GeoDataFrame({'geometry': [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326")
    clip_box = box(10, 10, 20, 20)
    clipped = clip(points, clip_box)
    assert clipped.empty


@pytest.mark.parametrize('mask_fixture_name', mask_variants_single_rectangle)
class TestClipWithSingleRectangleGdf:

    def test_returns_gdf(self, point_gdf, mask, request):
        """Test that function returns a GeoDataFrame (or GDF-like) object."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(point_gdf, mask)
        assert isinstance(result, GeoDataFrame)

    def test_returns_series(self, point_gdf, mask, request):
        """Test that function returns a GeoSeries if GeoSeries is passed."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(point_gdf.geometry, mask)
        assert isinstance(result, GeoSeries)

    def test_clip_points(self, point_gdf, mask, request):
        """Test clipping a points GDF with a generic polygon geometry."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(point_gdf, mask)
        assert len(result) == 3
        assert all(result.geometry.geom_type == 'Point')

    def test_clip_points_geom_col_rename(self, point_gdf, mask, request):
        """Test clipping a points GDF with a generic polygon geometry."""
        mask = request.getfixturevalue(mask_fixture_name)
        gdf_geom_custom = point_gdf.rename(columns={'geometry': 'geom'}).set_geometry('geom')
        result = clip(gdf_geom_custom, mask)
        assert result.geometry.name == 'geom'

    def test_clip_poly(self, buffered_locations, mask, request):
        """Test clipping a polygon GDF with a generic polygon geometry."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(buffered_locations, mask)
        assert all(result.geometry.geom_type == 'Polygon')

    def test_clip_poly_geom_col_rename(self, buffered_locations, mask, request):
        """Test clipping a polygon GDF with a generic polygon geometry."""
        mask = request.getfixturevalue(mask_fixture_name)
        gdf_geom_custom = buffered_locations.rename(columns={'geometry': 'geom'}).set_geometry('geom')
        result = clip(gdf_geom_custom, mask)
        assert result.geometry.name == 'geom'

    def test_clip_poly_series(self, buffered_locations, mask, request):
        """Test clipping a polygon GDF with a generic polygon geometry."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(buffered_locations.geometry, mask)
        assert isinstance(result, GeoSeries)
        assert all(result.geom_type == 'Polygon')

    def test_clip_multipoly_keep_geom_type(self, multi_poly_gdf, mask, request):
        """Test a multi poly object where the return includes a sliver.
        Also the bounds of the object should == the bounds of the clip object
        if they fully overlap (as they do in these fixtures)."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(multi_poly_gdf, mask)
        assert all(result.geometry.geom_type == 'MultiPolygon')
        assert_index_equal(result.bounds, mask.bounds)

    def test_clip_multiline(self, multi_line, mask, request):
        """Test that clipping a multiline feature with a poly returns expected
        output."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(multi_line, mask)
        assert all(result.geometry.geom_type.isin(['MultiLineString', 'LineString']))

    def test_clip_multipoint(self, multi_point, mask, request):
        """Clipping a multipoint feature with a polygon works as expected.
        should return a geodataframe with a single multi point feature"""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(multi_point, mask)
        assert all(result.geometry.geom_type == 'MultiPoint')

    def test_clip_lines(self, two_line_gdf, mask, request):
        """Test what happens when you give the clip_extent a line GDF."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(two_line_gdf, mask)
        assert all(result.geometry.geom_type == 'LineString')

    def test_mixed_geom(self, mixed_gdf, mask, request):
        """Test clipping a mixed GeoDataFrame"""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(mixed_gdf, mask)
        assert set(result.geometry.geom_type) == {'Polygon', 'LineString'}

    def test_mixed_series(self, mixed_gdf, mask, request):
        """Test clipping a mixed GeoSeries"""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(mixed_gdf.geometry, mask)
        assert isinstance(result, GeoSeries)
        assert set(result.geom_type) == {'Polygon', 'LineString'}

    def test_clip_with_line_extra_geom(self, sliver_line, mask, request):
        """When the output of a clipped line returns a geom collection,
        and keep_geom_type is True, no geometry collections should be returned."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(sliver_line, mask, keep_geom_type=True)
        assert all(result.geometry.geom_type == 'LineString')

    def test_clip_no_box_overlap(self, pointsoutside_nooverlap_gdf, mask, request):
        """Test clip when intersection is empty and boxes do not overlap."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(pointsoutside_nooverlap_gdf, mask)
        assert result.empty

    def test_clip_box_overlap(self, pointsoutside_overlap_gdf, mask, request):
        """Test clip when intersection is empty and boxes do overlap."""
        mask = request.getfixturevalue(mask_fixture_name)
        result = clip(pointsoutside_overlap_gdf, mask)
        assert result.empty

    def test_warning_extra_geoms_mixed(self, mixed_gdf, mask, request):
        """Test the correct warnings are raised if keep_geom_type is
        called on a mixed GDF"""
        mask = request.getfixturevalue(mask_fixture_name)
        with pytest.warns(UserWarning, match="Geometry types of input geodataframe"):
            clip(mixed_gdf, mask, keep_geom_type=True)

    def test_warning_geomcoll(self, geomcol_gdf, mask, request):
        """Test the correct warnings are raised if keep_geom_type is
        called on a GDF with GeometryCollection"""
        mask = request.getfixturevalue(mask_fixture_name)
        with pytest.warns(UserWarning, match="Geometry types of input geodataframe"):
            clip(geomcol_gdf, mask, keep_geom_type=True)


def test_clip_line_keep_slivers(sliver_line, single_rectangle_gdf):
    """Test the correct output if a point is returned
    from a line only geometry type."""
    result = clip(sliver_line, single_rectangle_gdf, keep_geom_type=False)
    assert set(result.geometry.geom_type) == {'LineString', 'Point'}


def test_clip_multipoly_keep_slivers(multi_poly_gdf, single_rectangle_gdf):
    """Test a multi poly object where the return includes a sliver.
    Also the bounds of the object should == the bounds of the clip object
    if they fully overlap (as they do in these fixtures)."""
    result = clip(multi_poly_gdf, single_rectangle_gdf, keep_geom_type=False)
    assert set(result.geometry.geom_type) == {'Polygon', 'MultiPolygon'}
    assert_index_equal(result.bounds, single_rectangle_gdf.bounds)


def test_clip_with_polygon(single_rectangle_gdf):
    """Test clip when using a shapely object"""
    poly = Polygon([(0, 0), (1, 1), (1, 0)])
    gdf = GeoDataFrame({'geometry': [poly]}, crs="EPSG:4326")
    result = clip(gdf, single_rectangle_gdf.geometry.iloc[0])
    assert isinstance(result, GeoDataFrame)
    assert len(result) == 1


def test_clip_with_multipolygon(buffered_locations, single_rectangle_gdf):
    """Test clipping a polygon with a multipolygon."""
    multi = MultiPolygon([single_rectangle_gdf.geometry.iloc[0], Polygon([(2, 2), (3, 3), (3, 2)])])
    result = clip(buffered_locations, multi)
    assert isinstance(result, GeoDataFrame)
    assert all(result.geometry.geom_type == 'Polygon')


@pytest.mark.parametrize('mask_fixture_name', mask_variants_large_rectangle)
def test_clip_single_multipoly_no_extra_geoms(buffered_locations,
    mask_fixture_name, request):
    """When clipping a multi-polygon feature, no additional geom types
    should be returned."""
    mask = request.getfixturevalue(mask_fixture_name)
    result = clip(buffered_locations, mask)
    assert set(result.geometry.geom_type) == {'Polygon'}


@pytest.mark.filterwarnings('ignore:All-NaN slice encountered')
@pytest.mark.parametrize('mask', [Polygon(), (np.nan,) * 4, (np.nan, 0, np.
    nan, 1), GeoSeries([Polygon(), Polygon()], crs='EPSG:3857'), GeoSeries(
    [Polygon(), Polygon()], crs='EPSG:3857').to_frame(), GeoSeries([], crs=
    'EPSG:3857'), GeoSeries([], crs='EPSG:3857').to_frame()])
def test_clip_empty_mask(buffered_locations, mask):
    """Test that clipping with empty mask returns an empty result."""
    result = clip(buffered_locations, mask)
    assert result.empty


def test_clip_sorting(point_gdf2):
    """Test the sorting kwarg in clip"""
    box = Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)])
    result = clip(point_gdf2, box)
    assert_index_equal(result.index, point_gdf2.index[1:2])

    result_unsorted = clip(point_gdf2, box, keep_geom_type=True)
    assert_index_equal(result_unsorted.index, point_gdf2.index[1:2])
