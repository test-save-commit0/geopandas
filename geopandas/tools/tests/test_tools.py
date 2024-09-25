from shapely.geometry import LineString, MultiPoint, Point, Polygon
from geopandas import GeoSeries
from geopandas.tools import collect
import pytest


class TestTools:
    def test_collect_points(self):
        points = GeoSeries([Point(0, 0), Point(1, 1), Point(2, 2)])
        result = collect(points)
        assert isinstance(result, MultiPoint)
        assert len(result.geoms) == 3

    def test_collect_lines(self):
        lines = GeoSeries([LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])])
        result = collect(lines)
        assert isinstance(result, LineString)
        assert len(result.coords) == 3

    def test_collect_mixed(self):
        mixed = GeoSeries([Point(0, 0), LineString([(1, 1), (2, 2)]), Polygon([(0, 0), (1, 1), (1, 0)])])
        result = collect(mixed)
        assert isinstance(result, MultiPoint)
        assert len(result.geoms) == 3

    def test_collect_single(self):
        single = GeoSeries([Point(0, 0)])
        result = collect(single)
        assert isinstance(result, Point)

    def test_collect_empty(self):
        empty = GeoSeries([])
        result = collect(empty)
        assert result is None

    def test_collect_multi(self):
        points = GeoSeries([Point(0, 0), Point(1, 1), Point(2, 2)])
        result = collect(points, multi=True)
        assert isinstance(result, MultiPoint)
        assert len(result.geoms) == 3

    def test_collect_lines_multi(self):
        lines = GeoSeries([LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])])
        result = collect(lines, multi=True)
        assert isinstance(result, MultiPoint)
        assert len(result.geoms) == 4
