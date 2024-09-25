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
    gdf = request.getfixturevalue(test_dataset)
    tmp_file = str(tmpdir.join(f"test.{file_format}"))
    
    if file_format == "parquet":
        gdf.to_parquet(tmp_file)
        result = read_parquet(tmp_file)
    elif file_format == "feather":
        gdf.to_feather(tmp_file)
        result = read_feather(tmp_file)
    
    assert_geodataframe_equal(gdf, result)


def test_index(tmpdir, file_format, naturalearth_lowres):
    """Setting index=`True` should preserve index in output, and
    setting index=`False` should drop index from output.
    """
    gdf = naturalearth_lowres.set_index('name')
    tmp_file = str(tmpdir.join(f"test.{file_format}"))
    
    if file_format == "parquet":
        gdf.to_parquet(tmp_file, index=True)
        result_with_index = read_parquet(tmp_file)
        gdf.to_parquet(tmp_file, index=False)
        result_without_index = read_parquet(tmp_file)
    elif file_format == "feather":
        gdf.to_feather(tmp_file, index=True)
        result_with_index = read_feather(tmp_file)
        gdf.to_feather(tmp_file, index=False)
        result_without_index = read_feather(tmp_file)
    
    assert_geodataframe_equal(gdf, result_with_index)
    assert result_without_index.index.name is None
    assert_geodataframe_equal(gdf.reset_index(drop=True), result_without_index)


def test_column_order(tmpdir, file_format, naturalearth_lowres):
    """The order of columns should be preserved in the output."""
    gdf = naturalearth_lowres[['name', 'pop_est', 'continent', 'geometry']]
    tmp_file = str(tmpdir.join(f"test.{file_format}"))
    
    if file_format == "parquet":
        gdf.to_parquet(tmp_file)
        result = read_parquet(tmp_file)
    elif file_format == "feather":
        gdf.to_feather(tmp_file)
        result = read_feather(tmp_file)
    
    assert list(gdf.columns) == list(result.columns)


@pytest.mark.parametrize('compression', ['snappy', 'gzip', 'brotli', None])
def test_parquet_compression(compression, tmpdir, naturalearth_lowres):
    """Using compression options should not raise errors, and should
    return identical GeoDataFrame.
    """
    tmp_file = str(tmpdir.join("test.parquet"))
    naturalearth_lowres.to_parquet(tmp_file, compression=compression)
    result = read_parquet(tmp_file)
    assert_geodataframe_equal(naturalearth_lowres, result)


@pytest.mark.skipif(Version(pyarrow.__version__) < Version('0.17.0'),
    reason='Feather only supported for pyarrow >= 0.17')
@pytest.mark.parametrize('compression', ['uncompressed', 'lz4', 'zstd'])
def test_feather_compression(compression, tmpdir, naturalearth_lowres):
    """Using compression options should not raise errors, and should
    return identical GeoDataFrame.
    """
    tmp_file = str(tmpdir.join("test.feather"))
    naturalearth_lowres.to_feather(tmp_file, compression=compression)
    result = read_feather(tmp_file)
    assert_geodataframe_equal(naturalearth_lowres, result)


def test_parquet_multiple_geom_cols(tmpdir, file_format, naturalearth_lowres):
    """If multiple geometry columns are present when written to parquet,
    they should all be returned as such when read from parquet.
    """
    gdf = naturalearth_lowres.copy()
    gdf['geometry2'] = gdf.geometry.centroid
    tmp_file = str(tmpdir.join(f"test.{file_format}"))
    
    if file_format == "parquet":
        gdf.to_parquet(tmp_file)
        result = read_parquet(tmp_file)
    elif file_format == "feather":
        gdf.to_feather(tmp_file)
        result = read_feather(tmp_file)
    
    assert isinstance(result, GeoDataFrame)
    assert isinstance(result['geometry'], geopandas.GeoSeries)
    assert isinstance(result['geometry2'], geopandas.GeoSeries)
    assert_geodataframe_equal(gdf, result)


def test_parquet_missing_metadata(tmpdir, naturalearth_lowres):
    """Missing geo metadata, such as from a parquet file created
    from a pandas DataFrame, will raise a ValueError.
    """
    df = DataFrame(naturalearth_lowres.drop(columns=['geometry']))
    tmp_file = str(tmpdir.join("test.parquet"))
    df.to_parquet(tmp_file)
    
    with pytest.raises(ValueError, match="Missing geo metadata in Parquet file."):
        read_parquet(tmp_file)


def test_parquet_missing_metadata2(tmpdir):
    """Missing geo metadata, such as from a parquet file created
    from a pyarrow Table (which will also not contain pandas metadata),
    will raise a ValueError.
    """
    table = pyarrow.Table.from_arrays(
        [pyarrow.array([1, 2, 3]), pyarrow.array(['a', 'b', 'c'])],
        names=['col1', 'col2']
    )
    tmp_file = str(tmpdir.join("test.parquet"))
    pq.write_table(table, tmp_file)
    
    with pytest.raises(ValueError, match="Missing geo metadata in Parquet file."):
        read_parquet(tmp_file)


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
    tmp_file = str(tmpdir.join("test.parquet"))
    table = pyarrow.Table.from_pandas(naturalearth_lowres)
    
    # Write the parquet file with custom metadata
    pq.write_table(table, tmp_file, metadata=geo_meta)
    
    with pytest.raises(ValueError, match=error):
        read_parquet(tmp_file)


def test_subset_columns(tmpdir, file_format, naturalearth_lowres):
    """Reading a subset of columns should correctly decode selected geometry
    columns.
    """
    gdf = naturalearth_lowres
    tmp_file = str(tmpdir.join(f"test.{file_format}"))
    
    if file_format == "parquet":
        gdf.to_parquet(tmp_file)
        result = read_parquet(tmp_file, columns=['name', 'geometry'])
    elif file_format == "feather":
        gdf.to_feather(tmp_file)
        result = read_feather(tmp_file, columns=['name', 'geometry'])
    
    expected = gdf[['name', 'geometry']]
    assert_geodataframe_equal(expected, result)


def test_promote_secondary_geometry(tmpdir, file_format, naturalearth_lowres):
    """Reading a subset of columns that does not include the primary geometry
    column should promote the first geometry column present.
    """
    gdf = naturalearth_lowres.copy()
    gdf['geometry2'] = gdf.geometry.centroid
    tmp_file = str(tmpdir.join(f"test.{file_format}"))
    
    if file_format == "parquet":
        gdf.to_parquet(tmp_file)
        result = read_parquet(tmp_file, columns=['name', 'geometry2'])
    elif file_format == "feather":
        gdf.to_feather(tmp_file)
        result = read_feather(tmp_file, columns=['name', 'geometry2'])
    
    assert isinstance(result, GeoDataFrame)
    assert result.geometry.name == 'geometry2'
    assert_geoseries_equal(gdf['geometry2'], result.geometry)


def test_columns_no_geometry(tmpdir, file_format, naturalearth_lowres):
    """Reading a parquet file that is missing all of the geometry columns
    should raise a ValueError"""
    gdf = naturalearth_lowres
    tmp_file = str(tmpdir.join(f"test.{file_format}"))
    
    if file_format == "parquet":
        gdf.to_parquet(tmp_file)
        with pytest.raises(ValueError, match="No geometry columns found"):
            read_parquet(tmp_file, columns=['name', 'pop_est'])
    elif file_format == "feather":
        gdf.to_feather(tmp_file)
        with pytest.raises(ValueError, match="No geometry columns found"):
            read_feather(tmp_file, columns=['name', 'pop_est'])


def test_missing_crs(tmpdir, file_format, naturalearth_lowres):
    """If CRS is `None`, it should be properly handled
    and remain `None` when read from parquet`.
    """
    gdf = naturalearth_lowres.copy()
    gdf.crs = None
    tmp_file = str(tmpdir.join(f"test.{file_format}"))
    
    if file_format == "parquet":
        gdf.to_parquet(tmp_file)
        result = read_parquet(tmp_file)
    elif file_format == "feather":
        gdf.to_feather(tmp_file)
        result = read_feather(tmp_file)
    
    assert result.crs is None
    assert_geodataframe_equal(gdf, result)


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
    feather_file = DATA_PATH / 'arrow' / f'test_data_v{version}.feather'
    parquet_file = DATA_PATH / 'arrow' / f'test_data_v{version}.parquet'
    
    gdf_feather = read_feather(feather_file)
    gdf_parquet = read_parquet(parquet_file)
    
    assert isinstance(gdf_feather, GeoDataFrame)
    assert isinstance(gdf_parquet, GeoDataFrame)
    assert gdf_feather.crs == "EPSG:4326"
    assert gdf_parquet.crs == "EPSG:4326"
    assert_geodataframe_equal(gdf_feather, gdf_parquet)


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
