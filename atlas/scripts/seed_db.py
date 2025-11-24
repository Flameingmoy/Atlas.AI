import random
import uuid
import h3
import duckdb
from shapely.geometry import Point, Polygon
import json
from app.core.db import get_db_connection, init_db

def generate_bangalore_data():
    conn = get_db_connection()
    
    # Clear existing data
    conn.execute("DELETE FROM pois")
    conn.execute("DELETE FROM demographics")
    
    # Bangalore, India approximate center
    bangalore_center = (12.9716, 77.5946)
    
    # 1. Generate Demographics (H3 Hexagons)
    # Get all hexes at res 9 within a ring of the center
    # v4 API: latlng_to_cell, grid_disk
    center_h3 = h3.latlng_to_cell(bangalore_center[0], bangalore_center[1], 9)
    h3_indices = h3.grid_disk(center_h3, 50)
    
    print(f"Seeding {len(h3_indices)} demographic hexes...")
    
    for h3_idx in h3_indices:
        pop_density = random.uniform(5000, 50000)
        income = random.uniform(10000, 80000)
        traffic = random.uniform(5, 10)
        
        # Get boundary polygon for visualization
        # v4 API: cell_to_boundary returns tuple of (lat, lon)
        boundary_coords = h3.cell_to_boundary(h3_idx) # (lat, lon)
        # Shapely expects (lon, lat), so swap
        boundary_coords_lonlat = [(c[1], c[0]) for c in boundary_coords]
        poly = Polygon(boundary_coords_lonlat)
        wkt_boundary = poly.wkt
        
        conn.execute("""
            INSERT INTO demographics (h3_index, population_density, median_income, traffic_score, boundary)
            VALUES (?, ?, ?, ?, ST_GeomFromText(?))
        """, (h3_idx, pop_density, int(income), traffic, wkt_boundary))
        
    # 2. Generate POIs
    categories = {
        "Coffee": ["Third Wave Coffee", "Starbucks", "Rameshwaram Cafe", "Blue Tokai"],
        "Gym": ["Cult.fit", "Gold's Gym", "Snap Fitness", "Volt Energy"],
        "Retail": ["Phoenix Marketcity", "Orion Mall", "More Supermarket", "Reliance Smart"]
    }
    
    print("Seeding 100 POIs...")
    for _ in range(100):
        cat = random.choice(list(categories.keys()))
        name = random.choice(categories[cat])
        
        lat = bangalore_center[0] + random.uniform(-0.05, 0.05)
        lon = bangalore_center[1] + random.uniform(-0.05, 0.05)
        
        point = Point(lon, lat)
        wkt_point = point.wkt
        
        meta = json.dumps({"rating": random.uniform(3.0, 5.0), "open_late": random.choice([True, False])})
        
        conn.execute("""
            INSERT INTO pois (id, name, category, subcategory, location, metadata_json)
            VALUES (?, ?, ?, ?, ST_GeomFromText(?), ?)
        """, (str(uuid.uuid4()), name, cat, cat, wkt_point, meta))
        
    conn.commit() # DuckDB auto-commits usually, but explicit is fine
    conn.close()
    print("Seeding Complete!")

if __name__ == "__main__":
    # Ensure tables exist
    init_db()
    generate_bangalore_data()
