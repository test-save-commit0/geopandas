"""
See generate_legacy_storage_files.py for the creation of the legacy files.

"""
import glob
import os
import pathlib
import pandas as pd
import pytest
from geopandas.testing import assert_geodataframe_equal
DATA_PATH = pathlib.Path(os.path.dirname(__file__)) / 'data'
files = glob.glob(str(DATA_PATH / 'pickle' / '*.pickle'))
