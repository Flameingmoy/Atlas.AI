import duckdb
import os
from pathlib import Path

# Get the project root directory (backend's parent)
# This allows the path to work regardless of where the script is run from
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
_DEFAULT_DB_PATH = str(_PROJECT_ROOT / "data" / "delhi.db")

DB_PATH = os.getenv("DATABASE_PATH", _DEFAULT_DB_PATH)

def get_db_connection():
    """
    Returns a DuckDB connection with spatial and h3 extensions loaded.
    """
    conn = duckdb.connect(DB_PATH)
    
    # Install and load extensions
    # Note: In production/persistent mode, install might only need to happen once.
    # But for safety in this prototype, we check/install.
    conn.install_extension("spatial")
    conn.load_extension("spatial")
    
    conn.install_extension("h3", repository="community")
    conn.load_extension("h3")
    
    return conn

def init_db():
    """
    Initializes the database schema for Delhi geographic data.
    Creates tables: delhi_area, delhi_city, delhi_pincode, delhi_points
    """
    conn = get_db_connection()
    
    # Create delhi_area table - Area/district boundaries
    conn.execute("""
        CREATE TABLE IF NOT EXISTS delhi_area (
            id INTEGER,
            name VARCHAR,
            geom GEOMETRY
        );
    """)
    
    # Create delhi_city table - City boundaries
    conn.execute("""
        CREATE TABLE IF NOT EXISTS delhi_city (
            id INTEGER,
            name VARCHAR,
            geom GEOMETRY
        );
    """)
    
    # Create delhi_pincode table - Pincode/postal code boundaries
    conn.execute("""
        CREATE TABLE IF NOT EXISTS delhi_pincode (
            id INTEGER,
            name VARCHAR,
            geom GEOMETRY
        );
    """)
    
    # Create delhi_points table - Points of interest
    conn.execute("""
        CREATE TABLE IF NOT EXISTS delhi_points (
            id INTEGER,
            name VARCHAR,
            category VARCHAR,
            geom GEOMETRY
        );
    """)
    
    conn.close()
    print("Database initialized successfully with Delhi schema.")
    print("Tables created: delhi_area, delhi_city, delhi_pincode, delhi_points")

if __name__ == "__main__":
    init_db()
