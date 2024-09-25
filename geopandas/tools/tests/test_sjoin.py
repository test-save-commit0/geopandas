import math
from typing import Sequence
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import GeometryCollection, Point, Polygon, box
import geopandas
import geopandas._compat as compat
from geopandas import GeoDataFrame, GeoSeries, points_from_xy, read_file, sjoin, sjoin_nearest
import pytest
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal
from pandas.testing import assert_frame_equal, assert_index_equal, assert_series_equal


class TestSpatialJoin:
    def test_spatial_join(self):
        # Create sample GeoDataFrames
        left_gdf = GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)],
            'value': [1, 2, 3]
        })
        right_gdf = GeoDataFrame({
            'geometry': [Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]), 
                         Polygon([(1, 1), (1, 2), (2, 2), (2, 1)])],
            'attr': ['A', 'B']
        })

        # Perform spatial join
        result = sjoin(left_gdf, right_gdf, how='left', predicate='intersects')

        # Assert the result
        expected = GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)],
            'value': [1, 2, 3],
            'index_right': [0, 1, 1],
            'attr': ['A', 'B', 'B']
        })
        assert_geodataframe_equal(result, expected)


class TestIndexNames:
    def test_index_names(self):
        # Create sample GeoDataFrames with named indexes
        left_gdf = GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1)],
            'value': [1, 2]
        }, index=pd.Index(['a', 'b'], name='left_idx'))
        right_gdf = GeoDataFrame({
            'geometry': [Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])],
            'attr': ['A']
        }, index=pd.Index(['x'], name='right_idx'))

        # Perform spatial join
        result = sjoin(left_gdf, right_gdf, how='left', predicate='intersects')

        # Assert the result
        assert result.index.name == 'left_idx'
        assert 'index_right' in result.columns
        assert_series_equal(result['index_right'], pd.Series(['x', 'x'], name='index_right', index=['a', 'b']))


@pytest.mark.usefixtures('_setup_class_nybb_filename')
class TestSpatialJoinNYBB:

    @pytest.mark.parametrize('predicate', ['intersects', 'within', 'contains'])
    def test_sjoin_no_valid_geoms(self, predicate):
        """Tests a completely empty GeoDataFrame."""
        empty_df = GeoDataFrame(geometry=[])
        nybb = read_file(self.nybb_filename)
        
        # Test empty left GeoDataFrame
        result_left = sjoin(empty_df, nybb, how='left', predicate=predicate)
        assert len(result_left) == 0
        assert set(result_left.columns) == set(empty_df.columns).union(nybb.columns).union(['index_right'])

        # Test empty right GeoDataFrame
        result_right = sjoin(nybb, empty_df, how='left', predicate=predicate)
        assert len(result_right) == len(nybb)
        assert set(result_right.columns) == set(nybb.columns).union(empty_df.columns).union(['index_right'])
        assert result_right['index_right'].isna().all()


class TestNearest:
    def test_nearest_join(self):
        # Create sample GeoDataFrames
        left_gdf = GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)],
            'value': [1, 2, 3]
        })
        right_gdf = GeoDataFrame({
            'geometry': [Point(0.1, 0.1), Point(1.1, 1.1), Point(2.1, 2.1)],
            'attr': ['A', 'B', 'C']
        })

        # Perform nearest join
        result = sjoin_nearest(left_gdf, right_gdf, how='left')

        # Assert the result
        expected = GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)],
            'value': [1, 2, 3],
            'index_right': [0, 1, 2],
            'attr': ['A', 'B', 'C']
        })
        assert_geodataframe_equal(result, expected)
