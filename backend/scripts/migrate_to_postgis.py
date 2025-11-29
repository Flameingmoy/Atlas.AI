#!/usr/bin/env python3
"""
Migration script to transfer data from DuckDB to PostGIS.
Run this after the PostGIS container is up and healthy.

Usage:
    python migrate_to_postgis.py
    
Or from docker:
    docker compose exec backend python -m scripts.migrate_to_postgis
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
import psycopg2
from psycopg2.extras import execute_values

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")  # Default to 5433 for local dev (docker mapped port)
DB_USER = os.getenv("DB_USER", "atlas")
DB_PASSWORD = os.getenv("DB_PASSWORD", "atlas_secret")
DB_NAME = os.getenv("DB_NAME", "atlas_db")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/app/data/delhi.db")

# Fallback for local development
if not Path(DUCKDB_PATH).exists():
    DUCKDB_PATH = str(Path(__file__).parent.parent.parent / "data" / "delhi.db")


def get_duckdb_connection():
    """Get DuckDB connection with spatial extension."""
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    conn.install_extension("spatial")
    conn.load_extension("spatial")
    return conn


def get_postgis_connection():
    """Get PostGIS connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def init_postgis_schema(pg_conn):
    """Create PostGIS schema with all required tables."""
    cursor = pg_conn.cursor()
    
    # Enable PostGIS
    cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    
    # Drop existing tables to ensure clean migration
    tables = [
        'points_super', 'points_pincode', 'points_in_city',
        'points_area', 'area_scores', 'area_with_centroid',
        'delhi_points', 'delhi_pincode', 'delhi_area', 'delhi_city'
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
    
    # Create delhi_city table
    cursor.execute("""
        CREATE TABLE delhi_city (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            geom GEOMETRY(GEOMETRY, 4326)
        );
    """)
    
    # Create delhi_area table
    cursor.execute("""
        CREATE TABLE delhi_area (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            geom GEOMETRY(GEOMETRY, 4326)
        );
    """)
    
    # Create delhi_pincode table
    cursor.execute("""
        CREATE TABLE delhi_pincode (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50),
            geom GEOMETRY(GEOMETRY, 4326)
        );
    """)
    
    # Create delhi_points table
    cursor.execute("""
        CREATE TABLE delhi_points (
            id SERIAL PRIMARY KEY,
            name VARCHAR(500),
            category VARCHAR(255),
            geom GEOMETRY(POINT, 4326)
        );
    """)
    
    # Create area_with_centroid table
    cursor.execute("""
        CREATE TABLE area_with_centroid (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            longitude DOUBLE PRECISION,
            latitude DOUBLE PRECISION
        );
    """)
    
    # Create area_scores table
    cursor.execute("""
        CREATE TABLE area_scores (
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
    
    # Create points_area table
    cursor.execute("""
        CREATE TABLE points_area (
            id SERIAL PRIMARY KEY,
            name VARCHAR(500),
            category VARCHAR(255),
            geom GEOMETRY(POINT, 4326),
            area VARCHAR(255)
        );
    """)
    
    # Create points_in_city table (points within city boundary, no extra columns)
    cursor.execute("""
        CREATE TABLE points_in_city (
            id SERIAL PRIMARY KEY,
            name VARCHAR(500),
            category VARCHAR(255),
            geom GEOMETRY(POINT, 4326)
        );
    """)
    
    # Create points_pincode table
    cursor.execute("""
        CREATE TABLE points_pincode (
            id SERIAL PRIMARY KEY,
            name VARCHAR(500),
            category VARCHAR(255),
            geom GEOMETRY(POINT, 4326),
            pincode VARCHAR(50)
        );
    """)
    
    # Create points_super table (points with super_category)
    cursor.execute("""
        CREATE TABLE points_super (
            id SERIAL PRIMARY KEY,
            name VARCHAR(500),
            category VARCHAR(255),
            geom GEOMETRY(POINT, 4326),
            super_category VARCHAR(255)
        );
    """)
    
    pg_conn.commit()
    print("PostGIS schema created.")


def migrate_geometry_table(duck_conn, pg_conn, table_name, pg_table_name=None):
    """Migrate a geometry table from DuckDB to PostGIS."""
    pg_table = pg_table_name or table_name
    cursor = pg_conn.cursor()
    
    try:
        # Get data from DuckDB with geometry as WKT
        query = f"SELECT id, name, ST_AsText(geom) as geom_wkt FROM {table_name}"
        rows = duck_conn.execute(query).fetchall()
        
        if not rows:
            print(f"  No data in {table_name}")
            return 0
        
        # Insert into PostGIS
        insert_sql = f"""
            INSERT INTO {pg_table} (id, name, geom)
            VALUES %s
        """
        
        # Convert WKT to PostGIS geometry
        values = []
        for row in rows:
            id_val, name, geom_wkt = row
            if geom_wkt:
                values.append((id_val, name, f"SRID=4326;{geom_wkt}"))
        
        if values:
            execute_values(
                cursor,
                f"INSERT INTO {pg_table} (id, name, geom) VALUES %s",
                values,
                template="(%s, %s, ST_GeomFromEWKT(%s))"
            )
        
        pg_conn.commit()
        print(f"  Migrated {len(values)} rows from {table_name} -> {pg_table}")
        return len(values)
        
    except Exception as e:
        print(f"  Error migrating {table_name}: {e}")
        pg_conn.rollback()
        return 0


def migrate_points_table(duck_conn, pg_conn):
    """Migrate delhi_points table."""
    cursor = pg_conn.cursor()
    
    try:
        query = """
            SELECT id, name, category, ST_AsText(geom) as geom_wkt 
            FROM delhi_points
        """
        rows = duck_conn.execute(query).fetchall()
        
        if not rows:
            print("  No data in delhi_points")
            return 0
        
        # Batch insert
        values = []
        for row in rows:
            id_val, name, category, geom_wkt = row
            if geom_wkt:
                values.append((id_val, name, category, f"SRID=4326;{geom_wkt}"))
        
        if values:
            execute_values(
                cursor,
                "INSERT INTO delhi_points (id, name, category, geom) VALUES %s",
                values,
                template="(%s, %s, %s, ST_GeomFromEWKT(%s))",
                page_size=5000
            )
        
        pg_conn.commit()
        print(f"  Migrated {len(values)} rows from delhi_points")
        return len(values)
        
    except Exception as e:
        print(f"  Error migrating delhi_points: {e}")
        pg_conn.rollback()
        return 0


def migrate_area_with_centroid(duck_conn, pg_conn):
    """Migrate areaWithCentroid table."""
    cursor = pg_conn.cursor()
    
    try:
        query = "SELECT id, name, longitude, latitude FROM areaWithCentroid"
        rows = duck_conn.execute(query).fetchall()
        
        if not rows:
            print("  No data in areaWithCentroid")
            return 0
        
        execute_values(
            cursor,
            "INSERT INTO area_with_centroid (id, name, longitude, latitude) VALUES %s",
            rows
        )
        
        pg_conn.commit()
        print(f"  Migrated {len(rows)} rows from areaWithCentroid -> area_with_centroid")
        return len(rows)
        
    except Exception as e:
        print(f"  Error migrating areaWithCentroid: {e}")
        pg_conn.rollback()
        return 0


def migrate_area_scores(duck_conn, pg_conn):
    """Migrate areaScores table."""
    cursor = pg_conn.cursor()
    
    try:
        query = """
            SELECT id, name, longitude, latitude,
                   Score_Population_Density, Score_Footfall, Score_Transit,
                   Score_Traffic, Score_Rent_Value, Score_Parking,
                   Score_Night_Activity, Score_Walkability, Score_Safety, Score_POI_Synergy
            FROM areaScores
        """
        rows = duck_conn.execute(query).fetchall()
        
        if not rows:
            print("  No data in areaScores")
            return 0
        
        execute_values(
            cursor,
            """INSERT INTO area_scores 
               (id, name, longitude, latitude, 
                score_population_density, score_footfall, score_transit,
                score_traffic, score_rent_value, score_parking,
                score_night_activity, score_walkability, score_safety, score_poi_synergy) 
               VALUES %s""",
            rows
        )
        
        pg_conn.commit()
        print(f"  Migrated {len(rows)} rows from areaScores -> area_scores")
        return len(rows)
        
    except Exception as e:
        print(f"  Error migrating areaScores: {e}")
        pg_conn.rollback()
        return 0


def migrate_points_area(duck_conn, pg_conn):
    """Migrate pointsArea table (handles duplicates by taking first occurrence)."""
    cursor = pg_conn.cursor()
    
    try:
        # Use ROW_NUMBER to deduplicate by id
        query = """
            WITH ranked AS (
                SELECT id, name, category, ST_AsText(geom) as geom_wkt, area,
                       ROW_NUMBER() OVER (PARTITION BY id ORDER BY id) as rn
                FROM pointsArea
            )
            SELECT id, name, category, geom_wkt, area
            FROM ranked WHERE rn = 1
        """
        rows = duck_conn.execute(query).fetchall()
        
        if not rows:
            print("  No data in pointsArea")
            return 0
        
        values = []
        for row in rows:
            id_val, name, category, geom_wkt, area = row
            if geom_wkt:
                values.append((id_val, name, category, f"SRID=4326;{geom_wkt}", area))
        
        if values:
            execute_values(
                cursor,
                "INSERT INTO points_area (id, name, category, geom, area) VALUES %s",
                values,
                template="(%s, %s, %s, ST_GeomFromEWKT(%s), %s)",
                page_size=5000
            )
        
        pg_conn.commit()
        print(f"  Migrated {len(values)} rows from pointsArea -> points_area")
        return len(values)
        
    except Exception as e:
        print(f"  Error migrating pointsArea: {e}")
        pg_conn.rollback()
        return 0


def migrate_points_in_city(duck_conn, pg_conn):
    """Migrate pointsInCity table."""
    cursor = pg_conn.cursor()
    
    try:
        query = """
            SELECT id, name, category, ST_AsText(geom) as geom_wkt 
            FROM pointsInCity
        """
        rows = duck_conn.execute(query).fetchall()
        
        if not rows:
            print("  No data in pointsInCity")
            return 0
        
        values = []
        for row in rows:
            id_val, name, category, geom_wkt = row
            if geom_wkt:
                values.append((id_val, name, category, f"SRID=4326;{geom_wkt}"))
        
        if values:
            execute_values(
                cursor,
                "INSERT INTO points_in_city (id, name, category, geom) VALUES %s",
                values,
                template="(%s, %s, %s, ST_GeomFromEWKT(%s))",
                page_size=5000
            )
        
        pg_conn.commit()
        print(f"  Migrated {len(values)} rows from pointsInCity -> points_in_city")
        return len(values)
        
    except Exception as e:
        print(f"  Error migrating pointsInCity: {e}")
        pg_conn.rollback()
        return 0


def migrate_points_pincode(duck_conn, pg_conn):
    """Migrate pointsPincode table."""
    cursor = pg_conn.cursor()
    
    try:
        query = """
            SELECT id, name, category, ST_AsText(geom) as geom_wkt, pincode 
            FROM pointsPincode
        """
        rows = duck_conn.execute(query).fetchall()
        
        if not rows:
            print("  No data in pointsPincode")
            return 0
        
        values = []
        for row in rows:
            id_val, name, category, geom_wkt, pincode = row
            if geom_wkt:
                values.append((id_val, name, category, f"SRID=4326;{geom_wkt}", pincode))
        
        if values:
            execute_values(
                cursor,
                "INSERT INTO points_pincode (id, name, category, geom, pincode) VALUES %s",
                values,
                template="(%s, %s, %s, ST_GeomFromEWKT(%s), %s)",
                page_size=5000
            )
        
        pg_conn.commit()
        print(f"  Migrated {len(values)} rows from pointsPincode -> points_pincode")
        return len(values)
        
    except Exception as e:
        print(f"  Error migrating pointsPincode: {e}")
        pg_conn.rollback()
        return 0


def migrate_points_super(duck_conn, pg_conn):
    """Migrate pointsSuper table."""
    cursor = pg_conn.cursor()
    
    try:
        query = """
            SELECT id, name, category, ST_AsText(geom) as geom_wkt, super_category 
            FROM pointsSuper
        """
        rows = duck_conn.execute(query).fetchall()
        
        if not rows:
            print("  No data in pointsSuper")
            return 0
        
        values = []
        for row in rows:
            id_val, name, category, geom_wkt, super_category = row
            if geom_wkt:
                values.append((id_val, name, category, f"SRID=4326;{geom_wkt}", super_category))
        
        if values:
            execute_values(
                cursor,
                "INSERT INTO points_super (id, name, category, geom, super_category) VALUES %s",
                values,
                template="(%s, %s, %s, ST_GeomFromEWKT(%s), %s)",
                page_size=5000
            )
        
        pg_conn.commit()
        print(f"  Migrated {len(values)} rows from pointsSuper -> points_super")
        return len(values)
        
    except Exception as e:
        print(f"  Error migrating pointsSuper: {e}")
        pg_conn.rollback()
        return 0


def create_spatial_indexes(pg_conn):
    """Create spatial and regular indexes for performance."""
    cursor = pg_conn.cursor()
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_delhi_city_geom ON delhi_city USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_delhi_area_geom ON delhi_area USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_delhi_pincode_geom ON delhi_pincode USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_delhi_points_geom ON delhi_points USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_points_area_geom ON points_area USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_points_in_city_geom ON points_in_city USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_points_pincode_geom ON points_pincode USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_points_super_geom ON points_super USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_area_with_centroid_name ON area_with_centroid(LOWER(name));",
        "CREATE INDEX IF NOT EXISTS idx_area_scores_name ON area_scores(name);",
        "CREATE INDEX IF NOT EXISTS idx_points_area_area ON points_area(area);",
        "CREATE INDEX IF NOT EXISTS idx_delhi_points_category ON delhi_points(category);",
        "CREATE INDEX IF NOT EXISTS idx_points_pincode_pincode ON points_pincode(pincode);",
        "CREATE INDEX IF NOT EXISTS idx_points_super_super_category ON points_super(super_category);",
    ]
    
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
        except Exception as e:
            print(f"  Warning creating index: {e}")
    
    pg_conn.commit()
    print("Spatial indexes created.")


def run_migration():
    """Run the full migration from DuckDB to PostGIS."""
    print("=" * 60)
    print("DuckDB -> PostGIS Migration")
    print("=" * 60)
    
    print(f"\nDuckDB path: {DUCKDB_PATH}")
    print(f"PostGIS: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    if not Path(DUCKDB_PATH).exists():
        print(f"\nERROR: DuckDB file not found at {DUCKDB_PATH}")
        sys.exit(1)
    
    print("\nConnecting to databases...")
    duck_conn = get_duckdb_connection()
    pg_conn = get_postgis_connection()
    
    print("\nInitializing PostGIS schema...")
    init_postgis_schema(pg_conn)
    
    print("\nMigrating tables...")
    
    # Migrate geometry tables
    migrate_geometry_table(duck_conn, pg_conn, "delhi_city")
    migrate_geometry_table(duck_conn, pg_conn, "delhi_area")
    migrate_geometry_table(duck_conn, pg_conn, "delhi_pincode")
    
    # Migrate points
    migrate_points_table(duck_conn, pg_conn)
    
    # Migrate derived tables
    migrate_area_with_centroid(duck_conn, pg_conn)
    migrate_area_scores(duck_conn, pg_conn)
    migrate_points_area(duck_conn, pg_conn)
    migrate_points_in_city(duck_conn, pg_conn)
    migrate_points_pincode(duck_conn, pg_conn)
    migrate_points_super(duck_conn, pg_conn)
    
    print("\nCreating indexes...")
    create_spatial_indexes(pg_conn)
    
    # Verify migration
    print("\nVerifying migration...")
    cursor = pg_conn.cursor()
    tables = [
        'delhi_city', 'delhi_area', 'delhi_pincode', 'delhi_points',
        'area_with_centroid', 'area_scores', 'points_area',
        'points_in_city', 'points_pincode', 'points_super'
    ]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    
    duck_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
