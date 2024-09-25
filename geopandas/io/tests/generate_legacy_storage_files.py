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
    # Create a simple GeoDataFrame
    df = pd.DataFrame({
        'name': ['Point A', 'Point B', 'Point C'],
        'value': [1, 2, 3]
    })
    geometry = [Point(0, 0), Point(1, 1), Point(2, 2)]
    gdf = geopandas.GeoDataFrame(df, geometry=geometry)
    return gdf

def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_legacy_storage_files.py <output_dir> <storage_format>")
        sys.exit(1)

    output_dir = sys.argv[1]
    storage_format = sys.argv[2]

    if storage_format != 'pickle':
        print("Only 'pickle' storage format is supported.")
        sys.exit(1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    data = create_pickle_data()
    
    # Generate filename based on Python version and platform
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    platform_name = platform.platform().lower()
    filename = f"gdf-{py_version}-{platform_name}.pickle"
    
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    print(f"Pickle file created: {filepath}")

if __name__ == '__main__':
    main()
