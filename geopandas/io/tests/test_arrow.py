from __future__ import absolute_import
import json
import os
import pathlib
from itertools import product
from packaging.version import Version
import numpy as np
from pandas import DataFrame
from pandas import read_parquet as pd_read_parquet
import shapely
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
import geopandas
from geopandas import GeoDataFrame, read_feather, read_file, read_parquet
from geopandas._compat import HAS_PYPROJ
from geopandas.array import to_wkb
from geopandas.io.arrow import METADATA_VERSION, SUPPORTED_VERSIONS, _convert_bbox_to_parquet_filter, _create_metadata, _decode_metadata, _encode_metadata, _geopandas_to_arrow, _get_filesystem_path, _remove_id_from_member_of_ensembles, _validate_dataframe, _validate_geo_metadata
import pytest
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal
from geopandas.tests.util import mock
from pandas.testing import assert_frame_equal
DATA_PATH = pathlib.Path(os.path.dirname(__file__)) / 'data'
pyarrow = pytest.importorskip('pyarrow')
import pyarrow.compute as pc
import pyarrow.parquet as pq
from pyarrow import feather


@pytest.mark.parametrize('test_dataset', ['naturalearth_lowres',
    'naturalearth_cities', 'nybb_filename'])
def test_roundtrip(tmpdir, file_format, test_dataset, request):
    """Writing to parquet should not raise errors, and should not alter original
    GeoDataFrame
    """
    pass


def test_index(tmpdir, file_format, naturalearth_lowres):
    """Setting index=`True` should preserve index in output, and
    setting index=`False` should drop index from output.
    """
    pass


def test_column_order(tmpdir, file_format, naturalearth_lowres):
    """The order of columns should be preserved in the output."""
    pass


@pytest.mark.parametrize('compression', ['snappy', 'gzip', 'brotli', None])
def test_parquet_compression(compression, tmpdir, naturalearth_lowres):
    """Using compression options should not raise errors, and should
    return identical GeoDataFrame.
    """
    pass


@pytest.mark.skipif(Version(pyarrow.__version__) < Version('0.17.0'),
    reason='Feather only supported for pyarrow >= 0.17')
@pytest.mark.parametrize('compression', ['uncompressed', 'lz4', 'zstd'])
def test_feather_compression(compression, tmpdir, naturalearth_lowres):
    """Using compression options should not raise errors, and should
    return identical GeoDataFrame.
    """
    pass


def test_parquet_multiple_geom_cols(tmpdir, file_format, naturalearth_lowres):
    """If multiple geometry columns are present when written to parquet,
    they should all be returned as such when read from parquet.
    """
    pass


def test_parquet_missing_metadata(tmpdir, naturalearth_lowres):
    """Missing geo metadata, such as from a parquet file created
    from a pandas DataFrame, will raise a ValueError.
    """
    pass


def test_parquet_missing_metadata2(tmpdir):
    """Missing geo metadata, such as from a parquet file created
    from a pyarrow Table (which will also not contain pandas metadata),
    will raise a ValueError.
    """
    pass


@pytest.mark.parametrize('geo_meta,error', [({'geo': b''},
    'Missing or malformed geo metadata in Parquet/Feather file'), ({'geo':
    _encode_metadata({})},
    'Missing or malformed geo metadata in Parquet/Feather file'), ({'geo':
    _encode_metadata({'foo': 'bar'})},
    "'geo' metadata in Parquet/Feather file is missing required key")])
def test_parquet_invalid_metadata(tmpdir, geo_meta, error, naturalearth_lowres
    ):
    """Has geo metadata with missing required fields will raise a ValueError.

    This requires writing the parquet file directly below, so that we can
    control the metadata that is written for this test.
    """
    pass


def test_subset_columns(tmpdir, file_format, naturalearth_lowres):
    """Reading a subset of columns should correctly decode selected geometry
    columns.
    """
    pass


def test_promote_secondary_geometry(tmpdir, file_format, naturalearth_lowres):
    """Reading a subset of columns that does not include the primary geometry
    column should promote the first geometry column present.
    """
    pass


def test_columns_no_geometry(tmpdir, file_format, naturalearth_lowres):
    """Reading a parquet file that is missing all of the geometry columns
    should raise a ValueError"""
    pass


def test_missing_crs(tmpdir, file_format, naturalearth_lowres):
    """If CRS is `None`, it should be properly handled
    and remain `None` when read from parquet`.
    """
    pass


@pytest.mark.parametrize('version', ['0.1.0', '0.4.0', '1.0.0-beta.1'])
def test_read_versioned_file(version):
    """
    Verify that files for different metadata spec versions can be read
    created for each supported version:

    # small dummy test dataset (not naturalearth_lowres, as this can change over time)
    from shapely.geometry import box, MultiPolygon
    df = geopandas.GeoDataFrame(
        {"col_str": ["a", "b"], "col_int": [1, 2], "col_float": [0.1, 0.2]},
        geometry=[MultiPolygon([box(0, 0, 1, 1), box(2, 2, 3, 3)]), box(4, 4, 5,5)],
        crs="EPSG:4326",
    )
    df.to_feather(DATA_PATH / 'arrow' / f'test_data_v{METADATA_VERSION}.feather')
    df.to_parquet(DATA_PATH / 'arrow' / f'test_data_v{METADATA_VERSION}.parquet')
    """
    pass


def test_read_gdal_files():
    """
    Verify that files written by GDAL can be read by geopandas.
    Since it is currently not yet straightforward to install GDAL with
    Parquet/Arrow enabled in our conda setup, we are testing with some
    generated files included in the repo (using GDAL 3.5.0):

    # small dummy test dataset (not naturalearth_lowres, as this can change over time)
    from shapely.geometry import box, MultiPolygon
    df = geopandas.GeoDataFrame(
        {"col_str": ["a", "b"], "col_int": [1, 2], "col_float": [0.1, 0.2]},
        geometry=[MultiPolygon([box(0, 0, 1, 1), box(2, 2, 3, 3)]), box(4, 4, 5,5)],
        crs="EPSG:4326",
    )
    df.to_file("test_data.gpkg", GEOMETRY_NAME="geometry")
    and then the gpkg file is converted to Parquet/Arrow with:
    $ ogr2ogr -f Parquet -lco FID= test_data_gdal350.parquet test_data.gpkg
    $ ogr2ogr -f Arrow -lco FID= -lco GEOMETRY_ENCODING=WKB test_data_gdal350.arrow test_data.gpkg

    Repeated for GDAL 3.9 which adds a bbox covering column:
    $ ogr2ogr -f Parquet -lco FID= test_data_gdal390.parquet test_data.gpkg
    """
    pass
