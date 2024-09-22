"""
Script to create the data and write legacy storage (pickle) files.

Based on pandas' generate_legacy_storage_files.py script.

To use this script, create an environment for which you want to
generate pickles, activate the environment, and run this script as:

$ python geopandas/geopandas/io/tests/generate_legacy_storage_files.py     geopandas/geopandas/io/tests/data/pickle/ pickle

This script generates a storage file for the current arch, system,

The idea here is you are using the *current* version of the
generate_legacy_storage_files with an *older* version of geopandas to
generate a pickle file. We will then check this file into a current
branch, and test using test_pickle.py. This will load the *older*
pickles and test versus the current data that is generated
(with master). These are then compared.

"""
import os
import pickle
import platform
import sys
import pandas as pd
from shapely.geometry import Point
import geopandas


def create_pickle_data():
    """create the pickle data"""
    pass


if __name__ == '__main__':
    main()
