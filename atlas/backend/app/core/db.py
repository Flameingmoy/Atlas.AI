import duckdb
import os

DB_PATH = "atlas.duckdb"

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
    Initializes the database schema.
    """
    conn = get_db_connection()
    
    # Create POIs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pois (
            id UUID PRIMARY KEY,
            name VARCHAR,
            category VARCHAR,
            subcategory VARCHAR,
            location GEOMETRY,
            metadata_json JSON
        );
    """)
    
    # Create Demographics table
    # Storing H3 index as string (VARCHAR) or UINT64. 
    # H3 extension usually works with UINT64 (H3Index).
    # Let's check docs or assume string for safety/readability first, 
    # but H3 functions might return uint64.
    # Let's use VARCHAR for the primary key to be safe with frontend JSON.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS demographics (
            h3_index VARCHAR PRIMARY KEY,
            population_density DOUBLE,
            median_income INTEGER,
            traffic_score DOUBLE,
            boundary GEOMETRY
        );
    """)
    
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
