import random
import uuid
import h3
from shapely.geometry import Point, Polygon
from geoalchemy2.shape import from_shape
from sqlmodel import Session, create_engine, SQLModel
from app.models.schema import POI, Demographic

# Database URL - Update this with your actual connection string
# For now, we'll use a placeholder or assume a local DB
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/atlas_db"

def create_db_and_tables():
    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    return engine

def generate_austin_data(engine):
    # Bangalore, India approximate center and bounds
    # Lat: 12.9716, Lon: 77.5946
    bangalore_center = (12.9716, 77.5946)
    
    # 1. Generate Demographics (H3 Hexagons)
    # Get all hexes at res 9 within a ring of the center
    h3_indices = h3.k_ring(h3.geo_to_h3(bangalore_center[0], bangalore_center[1], 9), 50)
    
    demographics = []
    for h3_idx in h3_indices:
        # Random data generation
        pop_density = random.uniform(5000, 50000) # Higher density for Bangalore
        income = random.uniform(10000, 80000) # Adjusted for INR/context (roughly)
        traffic = random.uniform(5, 10) # High traffic!
        
        # Get boundary polygon
        boundary_coords = h3.h3_to_geo_boundary(h3_idx, geo_json=True) # (lon, lat)
        # Shapely expects (lon, lat)
        poly = Polygon(boundary_coords)
        
        demo = Demographic(
            h3_index=h3_idx,
            population_density=pop_density,
            median_income=int(income),
            traffic_score=traffic,
            boundary=from_shape(poly, srid=4326)
        )
        demographics.append(demo)
        
    # 2. Generate POIs
    categories = {
        "Coffee": ["Third Wave Coffee", "Starbucks", "Rameshwaram Cafe", "Blue Tokai"],
        "Gym": ["Cult.fit", "Gold's Gym", "Snap Fitness", "Volt Energy"],
        "Retail": ["Phoenix Marketcity", "Orion Mall", "More Supermarket", "Reliance Smart"]
    }
    
    pois = []
    for _ in range(100): # 100 random POIs
        cat = random.choice(list(categories.keys()))
        name = random.choice(categories[cat])
        
        # Random location near Bangalore
        lat = bangalore_center[0] + random.uniform(-0.05, 0.05)
        lon = bangalore_center[1] + random.uniform(-0.05, 0.05)
        
        point = Point(lon, lat)
        
        poi = POI(
            name=name,
            category=cat,
            subcategory=cat, # Simplified for now
            location=from_shape(point, srid=4326),
            metadata_json={"rating": random.uniform(3.0, 5.0), "open_late": random.choice([True, False])}
        )
        pois.append(poi)

    # Save to DB
    with Session(engine) as session:
        print(f"Seeding {len(demographics)} demographic hexes...")
        session.add_all(demographics)
        print(f"Seeding {len(pois)} POIs...")
        session.add_all(pois)
        session.commit()
    
    print("Seeding Complete!")

if __name__ == "__main__":
    # Note: This requires the DB to exist. 
    # In a real run, we'd check/create the DB.
    try:
        engine = create_db_and_tables()
        generate_austin_data(engine)
    except Exception as e:
        print(f"Error seeding data: {e}")
        print("Ensure PostgreSQL is running and 'atlas_db' exists.")
