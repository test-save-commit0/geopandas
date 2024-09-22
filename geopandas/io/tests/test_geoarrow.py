import contextlib
import json
import os
import pathlib
from packaging.version import Version
import numpy as np
import shapely
from shapely import MultiPoint, Point, box
from geopandas import GeoDataFrame, GeoSeries
import pytest
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal
pytest.importorskip('pyarrow')
import pyarrow as pa
import pyarrow.compute as pc
from pyarrow import feather
DATA_PATH = pathlib.Path(os.path.dirname(__file__)) / 'data'
