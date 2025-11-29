import random
import duckdb
from shapely.geometry import Point, Polygon, MultiPolygon
import json
from app.core.db import get_db_connection, init_db

def generate_delhi_data():
    """
    Generate sample data for Delhi geographic database.
    Creates data for: delhi_area, delhi_city, delhi_pincode, delhi_points
    """
    conn = get_db_connection()
    
    # Clear existing data
    conn.execute("DELETE FROM delhi_area")
    conn.execute("DELETE FROM delhi_city")
    conn.execute("DELETE FROM delhi_pincode")
    conn.execute("DELETE FROM delhi_points")
    
    # Delhi, India center coordinates
    delhi_center = (28.6139, 77.2090)  # Lat, Lon
    
    print("Seeding Delhi geographic data...")
    
    # 1. Generate delhi_city (City boundary)
    print("Seeding delhi_city...")
    # Create a rough polygon around Delhi center (approximate boundary)
    city_boundary_coords = [
        (77.0, 28.4),   # Southwest
        (77.4, 28.4),   # Southeast
        (77.4, 28.9),   # Northeast
        (77.0, 28.9),   # Northwest
        (77.0, 28.4)    # Close polygon
    ]
    city_polygon = Polygon(city_boundary_coords)
    city_wkt = city_polygon.wkt
    
    conn.execute("""
        INSERT INTO delhi_city (id, name, geom)
        VALUES (?, ?, ST_GeomFromText(?))
    """, (1, "Delhi", city_wkt))
    
    # 2. Generate delhi_area (Districts/Areas)
    print("Seeding delhi_area...")
    delhi_areas = [
        "Central Delhi",
        "North Delhi",
        "South Delhi",
        "East Delhi",
        "West Delhi",
        "New Delhi",
        "North West Delhi",
        "North East Delhi",
        "South West Delhi",
        "South East Delhi",
        "Shahdara"
    ]
    
    for idx, area_name in enumerate(delhi_areas, start=1):
        # Generate a random polygon within Delhi for each area
        lat_offset = random.uniform(-0.15, 0.15)
        lon_offset = random.uniform(-0.15, 0.15)
        
        base_lat = delhi_center[0] + lat_offset
        base_lon = delhi_center[1] + lon_offset
        
        # Create a small polygon for the area
        area_coords = [
            (base_lon - 0.05, base_lat - 0.05),
            (base_lon + 0.05, base_lat - 0.05),
            (base_lon + 0.05, base_lat + 0.05),
            (base_lon - 0.05, base_lat + 0.05),
            (base_lon - 0.05, base_lat - 0.05)
        ]
        area_polygon = Polygon(area_coords)
        area_wkt = area_polygon.wkt
        
        conn.execute("""
            INSERT INTO delhi_area (id, name, geom)
            VALUES (?, ?, ST_GeomFromText(?))
        """, (idx, area_name, area_wkt))
    
    # 3. Generate delhi_pincode (Pincodes)
    print("Seeding delhi_pincode...")
    # Sample Delhi pincodes
    delhi_pincodes = [
        "110001", "110002", "110003", "110004", "110005",
        "110006", "110007", "110008", "110009", "110010",
        "110011", "110012", "110013", "110014", "110015",
        "110016", "110017", "110018", "110019", "110020",
        "110021", "110022", "110023", "110024", "110025",
        "110026", "110027", "110028", "110029", "110030"
    ]
    
    for idx, pincode in enumerate(delhi_pincodes, start=1):
        # Generate a random small polygon for each pincode area
        lat_offset = random.uniform(-0.2, 0.2)
        lon_offset = random.uniform(-0.2, 0.2)
        
        base_lat = delhi_center[0] + lat_offset
        base_lon = delhi_center[1] + lon_offset
        
        # Create a small polygon for the pincode area
        pin_coords = [
            (base_lon - 0.02, base_lat - 0.02),
            (base_lon + 0.02, base_lat - 0.02),
            (base_lon + 0.02, base_lat + 0.02),
            (base_lon - 0.02, base_lat + 0.02),
            (base_lon - 0.02, base_lat - 0.02)
        ]
        pin_polygon = Polygon(pin_coords)
        pin_wkt = pin_polygon.wkt
        
        conn.execute("""
            INSERT INTO delhi_pincode (id, name, geom)
            VALUES (?, ?, ST_GeomFromText(?))
        """, (idx, pincode, pin_wkt))
    
    # 4. Generate delhi_points (Points of Interest)
    print("Seeding delhi_points...")
    
    # Delhi-specific POI categories and names
    poi_categories = {
        "Restaurant": [
            "Karim's", "Bukhara", "Indian Accent", "Moti Mahal",
            "Paranthe Wali Gali", "Saravana Bhavan", "Haldiram's",
            "Bikanervala", "Kake Da Hotel", "Gulati Restaurant"
        ],
        "Cafe": [
            "Starbucks", "Cafe Coffee Day", "Blue Tokai Coffee",
            "Indian Coffee House", "Café Turtle", "Diva Spiced",
            "Chai Point", "Jugmug Thela", "Kunzum Travel Cafe"
        ],
        "Mall": [
            "Select Citywalk", "DLF Promenade", "Ambience Mall",
            "Pacific Mall", "Vegas Mall", "DLF Mall of India",
            "MGF Metropolitan Mall", "Ansal Plaza"
        ],
        "Monument": [
            "Red Fort", "Qutub Minar", "India Gate", "Humayun's Tomb",
            "Lotus Temple", "Akshardham Temple", "Jama Masjid",
            "Lodhi Garden", "Purana Qila", "Safdarjung Tomb"
        ],
        "Market": [
            "Chandni Chowk", "Sarojini Nagar", "Lajpat Nagar",
            "Connaught Place", "Khan Market", "Dilli Haat",
            "Janpath Market", "Karol Bagh", "Nehru Place"
        ],
        "Hospital": [
            "AIIMS", "Safdarjung Hospital", "Apollo Hospital",
            "Max Hospital", "Fortis Hospital", "Medanta",
            "BLK Hospital", "Sir Ganga Ram Hospital"
        ],
        "Metro Station": [
            "Rajiv Chowk", "Kashmere Gate", "Central Secretariat",
            "Chandni Chowk", "New Delhi", "Connaught Place",
            "Hauz Khas", "Nehru Place", "Dwarka Sector 21"
        ]
    }
    
    point_count = 200
    for idx in range(1, point_count + 1):
        category = random.choice(list(poi_categories.keys()))
        name = random.choice(poi_categories[category])
        
        # Generate random point within Delhi area
        lat = delhi_center[0] + random.uniform(-0.2, 0.2)
        lon = delhi_center[1] + random.uniform(-0.2, 0.2)
        
        point = Point(lon, lat)
        point_wkt = point.wkt
        
        conn.execute("""
            INSERT INTO delhi_points (id, name, category, geom)
            VALUES (?, ?, ?, ST_GeomFromText(?))
        """, (idx, name, category, point_wkt))
    
    conn.commit()
    conn.close()
    
    print(f"Seeding Complete!")
    print(f"  - 1 city boundary")
    print(f"  - {len(delhi_areas)} areas")
    print(f"  - {len(delhi_pincodes)} pincodes")
    print(f"  - {point_count} points of interest")

if __name__ == "__main__":
    # Ensure tables exist
    init_db()
    generate_delhi_data()
