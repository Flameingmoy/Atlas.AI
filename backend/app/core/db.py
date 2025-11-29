"""
Database connection module for PostGIS with connection pooling.
Supports concurrent reads for better UI performance.
"""
import os
from contextlib import contextmanager
from typing import Generator, Any
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# Database configuration from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "atlas")
DB_PASSWORD = os.getenv("DB_PASSWORD", "atlas_secret")
DB_NAME = os.getenv("DB_NAME", "atlas_db")
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Connection pool configuration
MIN_CONNECTIONS = 2
MAX_CONNECTIONS = 20

# Global connection pool (thread-safe)
_connection_pool: pool.ThreadedConnectionPool | None = None


def get_pool() -> pool.ThreadedConnectionPool:
    """
    Get or create the connection pool.
    Uses ThreadedConnectionPool for thread-safe concurrent access.
    """
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.ThreadedConnectionPool(
            MIN_CONNECTIONS,
            MAX_CONNECTIONS,
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
    return _connection_pool


@contextmanager
def get_db_connection() -> Generator[Any, None, None]:
    """
    Context manager for database connections.
    Automatically returns connection to pool when done.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    conn = None
    try:
        conn = get_pool().getconn()
        yield conn
    finally:
        if conn:
            get_pool().putconn(conn)


@contextmanager
def get_db_cursor(dict_cursor: bool = False) -> Generator[Any, None, None]:
    """
    Context manager that provides a cursor directly.
    Handles connection acquisition, cursor creation, commit, and cleanup.
    
    Args:
        dict_cursor: If True, returns rows as dictionaries instead of tuples
    
    Usage:
        with get_db_cursor(dict_cursor=True) as cursor:
            cursor.execute("SELECT * FROM table")
            rows = cursor.fetchall()
    """
    with get_db_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()


def execute_query(query: str, params: tuple = None, fetch: str = "all", dict_cursor: bool = False):
    """
    Execute a query and return results.
    
    Args:
        query: SQL query string (use %s for parameters)
        params: Query parameters as tuple
        fetch: "all", "one", or "none"
        dict_cursor: Return rows as dicts
    
    Returns:
        Query results based on fetch mode
    """
    with get_db_cursor(dict_cursor=dict_cursor) as cursor:
        cursor.execute(query, params)
        if fetch == "all":
            return cursor.fetchall()
        elif fetch == "one":
            return cursor.fetchone()
        return None


def init_pool():
    """Initialize the connection pool explicitly."""
    get_pool()


def close_pool():
    """Close all connections in the pool."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None


def init_postgis_schema():
    """
    Initialize PostGIS schema with required tables.
    Creates spatial indexes for performance.
    """
    with get_db_cursor() as cursor:
        # Enable PostGIS extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        
        # Create delhi_city table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS delhi_city (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                geom GEOMETRY(MULTIPOLYGON, 4326)
            );
        """)
        
        # Create delhi_area table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS delhi_area (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                geom GEOMETRY(MULTIPOLYGON, 4326)
            );
        """)
        
        # Create delhi_pincode table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS delhi_pincode (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50),
                geom GEOMETRY(MULTIPOLYGON, 4326)
            );
        """)
        
        # Create delhi_points table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS delhi_points (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500),
                category VARCHAR(255),
                geom GEOMETRY(POINT, 4326)
            );
        """)
        
        # Create areaWithCentroid view/table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS area_with_centroid (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                longitude DOUBLE PRECISION,
                latitude DOUBLE PRECISION
            );
        """)
        
        # Create areaScores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS area_scores (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                longitude DOUBLE PRECISION,
                latitude DOUBLE PRECISION,
                score_population_density DOUBLE PRECISION DEFAULT 0,
                score_footfall DOUBLE PRECISION DEFAULT 0,
                score_transit DOUBLE PRECISION DEFAULT 0,
                score_traffic DOUBLE PRECISION DEFAULT 0,
                score_rent_value DOUBLE PRECISION DEFAULT 0,
                score_parking DOUBLE PRECISION DEFAULT 0,
                score_night_activity DOUBLE PRECISION DEFAULT 0,
                score_walkability DOUBLE PRECISION DEFAULT 0,
                score_safety DOUBLE PRECISION DEFAULT 0,
                score_poi_synergy DOUBLE PRECISION DEFAULT 0
            );
        """)
        
        # Create points_area table (points with area mapping)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS points_area (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500),
                category VARCHAR(255),
                geom GEOMETRY(POINT, 4326),
                area VARCHAR(255)
            );
        """)
        
        # Create spatial indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_delhi_city_geom ON delhi_city USING GIST(geom);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_delhi_area_geom ON delhi_area USING GIST(geom);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_delhi_pincode_geom ON delhi_pincode USING GIST(geom);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_delhi_points_geom ON delhi_points USING GIST(geom);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_area_geom ON points_area USING GIST(geom);")
        
        # Create indexes on name columns for search
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_area_with_centroid_name ON area_with_centroid(name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_area_scores_name ON area_scores(name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_area_area ON points_area(area);")
        
    print("PostGIS schema initialized successfully.")


# Legacy DuckDB support (for migration)
def get_duckdb_connection():
    """
    Get a DuckDB connection for migration purposes.
    """
    import duckdb
    from pathlib import Path
    
    duckdb_path = os.getenv("DUCKDB_PATH", "/app/data/delhi.db")
    if not Path(duckdb_path).exists():
        # Fallback for local development
        backend_dir = Path(__file__).resolve().parent.parent.parent
        project_root = backend_dir.parent
        duckdb_path = str(project_root / "data" / "delhi.db")
    
    conn = duckdb.connect(duckdb_path)
    conn.install_extension("spatial")
    conn.load_extension("spatial")
    return conn


if __name__ == "__main__":
    init_postgis_schema()
