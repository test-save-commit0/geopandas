import os
from shapely.geometry import LineString, MultiLineString, MultiPoint, MultiPolygon, Point, Polygon
import geopandas
from geopandas import GeoDataFrame
from .test_file import FIONA_MARK, PYOGRIO_MARK
import pytest
from geopandas.testing import assert_geodataframe_equal
city_hall_boundaries = Polygon(((-73.5541107525234, 45.5091983609661), (-
    73.5546126200639, 45.5086813829106), (-73.5540185061397, 
    45.5084409343852), (-73.5539986525799, 45.5084323044531), (-
    73.5535801792994, 45.5089539203786), (-73.5541107525234, 45.5091983609661))
    )
vauquelin_place = Polygon(((-73.5542465586147, 45.5081555487952), (-
    73.5540185061397, 45.5084409343852), (-73.5546126200639, 
    45.5086813829106), (-73.5548825850032, 45.5084033554357), (-
    73.5542465586147, 45.5081555487952)))
city_hall_walls = [LineString(((-73.5541107525234, 45.5091983609661), (-
    73.5546126200639, 45.5086813829106), (-73.5540185061397, 
    45.5084409343852))), LineString(((-73.5539986525799, 45.5084323044531),
    (-73.5535801792994, 45.5089539203786), (-73.5541107525234, 
    45.5091983609661)))]
city_hall_entrance = Point(-73.553785, 45.508722)
city_hall_balcony = Point(-73.554138, 45.50908)
city_hall_council_chamber = Point(-73.554246, 45.508931)
point_3D = Point(-73.553785, 45.508722, 300)


class _ExpectedError:

    def __init__(self, error_type, error_message_match):
        self.type = error_type
        self.match = error_message_match


class _ExpectedErrorBuilder:

    def __init__(self, composite_key):
        self.composite_key = composite_key


_geodataframes_to_write = []
_expected_exceptions = {}
_CRS = 'epsg:4326'
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[city_hall_entrance,
    city_hall_balcony])
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[MultiPoint([
    city_hall_balcony, city_hall_council_chamber]), MultiPoint([
    city_hall_entrance, city_hall_balcony, city_hall_council_chamber])])
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[MultiPoint([
    city_hall_entrance, city_hall_balcony]), city_hall_balcony])
_geodataframes_to_write.append(gdf)
_expect_writing(gdf, 'ESRI Shapefile').to_raise(RuntimeError,
    'Failed to write record')
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=city_hall_walls)
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[MultiLineString(
    city_hall_walls), MultiLineString(city_hall_walls)])
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[MultiLineString(
    city_hall_walls), city_hall_walls[0]])
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[city_hall_boundaries,
    vauquelin_place])
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1]}, crs=_CRS, geometry=[MultiPolygon((
    city_hall_boundaries, vauquelin_place))])
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[MultiPolygon((
    city_hall_boundaries, vauquelin_place)), city_hall_boundaries])
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[None, city_hall_entrance]
    )
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[None, point_3D])
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2]}, crs=_CRS, geometry=[None, None])
_geodataframes_to_write.append(gdf)
gdf = GeoDataFrame({'a': [1, 2, 3, 4, 5, 6]}, crs=_CRS, geometry=[
    MultiPolygon((city_hall_boundaries, vauquelin_place)),
    city_hall_entrance, MultiLineString(city_hall_walls), city_hall_walls[0
    ], MultiPoint([city_hall_entrance, city_hall_balcony]), city_hall_balcony])
_geodataframes_to_write.append(gdf)
_expect_writing(gdf, 'ESRI Shapefile').to_raise(RuntimeError,
    'Failed to write record')
gdf = GeoDataFrame({'a': [1, 2, 3, 4, 5, 6, 7]}, crs=_CRS, geometry=[
    MultiPolygon((city_hall_boundaries, vauquelin_place)),
    city_hall_entrance, MultiLineString(city_hall_walls), city_hall_walls[0
    ], MultiPoint([city_hall_entrance, city_hall_balcony]),
    city_hall_balcony, point_3D])
_geodataframes_to_write.append(gdf)
_expect_writing(gdf, 'ESRI Shapefile').to_raise(RuntimeError,
    'Failed to write record')
