"""
Tests here include reading/writing to different types of spatial databases.
The spatial database tests may not work without additional system
configuration. postGIS tests require a test database to have been setup;
see geopandas.tests.util for more information.
"""
import os
import warnings
from importlib.util import find_spec
import pandas as pd
import geopandas
import geopandas._compat as compat
from geopandas import GeoDataFrame, read_file, read_postgis
from geopandas._compat import HAS_PYPROJ
from geopandas.io.sql import _get_conn as get_conn
from geopandas.io.sql import _write_postgis as write_postgis
import pytest
from geopandas.tests.util import create_postgis, create_spatialite, mock, validate_boro_df
try:
    from sqlalchemy import text
except ImportError:
    text = str


def check_available_postgis_drivers() ->list[str]:
    """Work out which of psycopg2 and psycopg are available.
    This prevents tests running if the relevant package isn't installed
    (rather than being skipped, as skips are treated as failures during postgis CI)
    """
    pass


POSTGIS_DRIVERS = check_available_postgis_drivers()


def prepare_database_credentials() ->dict:
    """Gather postgres connection credentials from environment variables."""
    pass


@pytest.fixture()
def connection_postgis(request):
    """Create a postgres connection using either psycopg2 or psycopg.

    Use this as an indirect fixture, where the request parameter is POSTGIS_DRIVERS."""
    pass


@pytest.fixture()
def engine_postgis(request):
    """
    Initiate a sqlalchemy connection engine using either psycopg2 or psycopg.

    Use this as an indirect fixture, where the request parameter is POSTGIS_DRIVERS.
    """
    pass


@pytest.fixture()
def connection_spatialite():
    """
    Return a memory-based SQLite3 connection with SpatiaLite enabled & initialized.

    `The sqlite3 module must be built with loadable extension support
    <https://docs.python.org/3/library/sqlite3.html#f1>`_ and
    `SpatiaLite <https://www.gaia-gis.it/fossil/libspatialite/index>`_
    must be available on the system as a SQLite module.
    Packages available on Anaconda meet requirements.

    Exceptions
    ----------
    ``AttributeError`` on missing support for loadable SQLite extensions
    ``sqlite3.OperationalError`` on missing SpatiaLite
    """
    pass


class TestIO:

    @pytest.mark.parametrize('connection_postgis', POSTGIS_DRIVERS,
        indirect=True)
    def test_read_postgis_select_geom_as(self, connection_postgis, df_nybb):
        """Tests that a SELECT {geom} AS {some_other_geom} works."""
        pass

    @pytest.mark.parametrize('connection_postgis', POSTGIS_DRIVERS,
        indirect=True)
    def test_read_postgis_get_srid(self, connection_postgis, df_nybb):
        """Tests that an SRID can be read from a geodatabase (GH #451)."""
        pass

    @pytest.mark.parametrize('connection_postgis', POSTGIS_DRIVERS,
        indirect=True)
    def test_read_postgis_override_srid(self, connection_postgis, df_nybb):
        """Tests that a user specified CRS overrides the geodatabase SRID."""
        pass

    def test_read_postgis_null_geom(self, connection_spatialite, df_nybb):
        """Tests that geometry with NULL is accepted."""
        pass

    def test_read_postgis_binary(self, connection_spatialite, df_nybb):
        """Tests that geometry read as binary is accepted."""
        pass

    @pytest.mark.parametrize('connection_postgis', POSTGIS_DRIVERS,
        indirect=True)
    def test_read_postgis_chunksize(self, connection_postgis, df_nybb):
        """Test chunksize argument"""
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_default(self, engine_postgis, df_nybb):
        """Tests that GeoDataFrame can be written to PostGIS with defaults."""
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_uppercase_tablename(self, engine_postgis, df_nybb):
        """Tests writing GeoDataFrame to PostGIS with uppercase tablename."""
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_sqlalchemy_connection(self, engine_postgis, df_nybb
        ):
        """Tests that GeoDataFrame can be written to PostGIS with defaults."""
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_fail_when_table_exists(self, engine_postgis, df_nybb
        ):
        """
        Tests that uploading the same table raises error when: if_replace='fail'.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_replace_when_table_exists(self, engine_postgis,
        df_nybb):
        """
        Tests that replacing a table is possible when: if_replace='replace'.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_append_when_table_exists(self, engine_postgis,
        df_nybb):
        """
        Tests that appending to existing table produces correct results when:
        if_replace='append'.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_without_crs(self, engine_postgis, df_nybb):
        """
        Tests that GeoDataFrame can be written to PostGIS without CRS information.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_with_esri_authority(self, engine_postgis, df_nybb):
        """
        Tests that GeoDataFrame can be written to PostGIS with ESRI Authority
        CRS information (GH #2414).
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_geometry_collection(self, engine_postgis,
        df_geom_collection):
        """
        Tests that writing a mix of different geometry types is possible.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_mixed_geometry_types(self, engine_postgis,
        df_mixed_single_and_multi):
        """
        Tests that writing a mix of single and MultiGeometries is possible.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_linear_ring(self, engine_postgis, df_linear_ring):
        """
        Tests that writing a LinearRing.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_in_chunks(self, engine_postgis,
        df_mixed_single_and_multi):
        """
        Tests writing a LinearRing works.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_to_different_schema(self, engine_postgis, df_nybb):
        """
        Tests writing data to alternative schema.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_to_different_schema_when_table_exists(self,
        engine_postgis, df_nybb):
        """
        Tests writing data to alternative schema.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_write_postgis_3D_geometries(self, engine_postgis, df_3D_geoms):
        """
        Tests writing a geometries with 3 dimensions works.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_row_order(self, engine_postgis, df_nybb):
        """
        Tests that the row order in db table follows the order of the original frame.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_append_before_table_exists(self, engine_postgis, df_nybb):
        """
        Tests that insert works with if_exists='append' when table does not exist yet.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    def test_append_with_different_crs(self, engine_postgis, df_nybb):
        """
        Tests that the warning is raised if table CRS differs from frame.
        """
        pass

    @pytest.mark.parametrize('engine_postgis', POSTGIS_DRIVERS, indirect=True)
    @pytest.mark.xfail(compat.PANDAS_GE_20 and not compat.PANDAS_GE_202,
        reason=
        'Duplicate columns are dropped in read_sql with pandas 2.0.0 and 2.0.1'
        )
    def test_duplicate_geometry_column_fails(self, engine_postgis):
        """
        Tests that a ValueError is raised if an SQL query returns two geometry columns.
        """
        pass

    @pytest.mark.parametrize('connection_postgis', POSTGIS_DRIVERS,
        indirect=True)
    def test_read_non_epsg_crs_chunksize(self, connection_postgis, df_nybb):
        """Test chunksize argument with non epsg crs"""
        pass
