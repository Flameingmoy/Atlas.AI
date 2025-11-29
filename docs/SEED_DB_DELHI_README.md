# Delhi Database Seed Script

## Overview

The `atlas/scripts/seed_db.py` script generates sample geographic data for Delhi across all 4 tables in the new schema.

---

## What Gets Seeded

### 1. **delhi_city** (1 record)
- **Delhi city boundary** - Large polygon covering the NCT area
- Approximate boundary: 77.0-77.4 longitude, 28.4-28.9 latitude

### 2. **delhi_area** (11 areas)
Districts/administrative areas:
- Central Delhi
- North Delhi
- South Delhi
- East Delhi
- West Delhi
- New Delhi
- North West Delhi
- North East Delhi
- South West Delhi
- South East Delhi
- Shahdara

Each area gets a randomly placed polygon within Delhi boundaries.

### 3. **delhi_pincode** (30 pincodes)
Sample Delhi pincodes from **110001** to **110030**
- Each pincode gets a small polygon representing its coverage area
- Randomly distributed across Delhi

### 4. **delhi_points** (200 POIs)
Points of Interest across 7 categories:

#### **Restaurant** (10 names)
- Karim's, Bukhara, Indian Accent, Moti Mahal
- Paranthe Wali Gali, Saravana Bhavan, Haldiram's
- Bikanervala, Kake Da Hotel, Gulati Restaurant

#### **Cafe** (9 names)
- Starbucks, Cafe Coffee Day, Blue Tokai Coffee
- Indian Coffee House, Café Turtle, Diva Spiced
- Chai Point, Jugmug Thela, Kunzum Travel Cafe

#### **Mall** (8 names)
- Select Citywalk, DLF Promenade, Ambience Mall
- Pacific Mall, Vegas Mall, DLF Mall of India
- MGF Metropolitan Mall, Ansal Plaza

#### **Monument** (10 names)
- Red Fort, Qutub Minar, India Gate, Humayun's Tomb
- Lotus Temple, Akshardham Temple, Jama Masjid
- Lodhi Garden, Purana Qila, Safdarjung Tomb

#### **Market** (9 names)
- Chandni Chowk, Sarojini Nagar, Lajpat Nagar
- Connaught Place, Khan Market, Dilli Haat
- Janpath Market, Karol Bagh, Nehru Place

#### **Hospital** (8 names)
- AIIMS, Safdarjung Hospital, Apollo Hospital
- Max Hospital, Fortis Hospital, Medanta
- BLK Hospital, Sir Ganga Ram Hospital

#### **Metro Station** (9 names)
- Rajiv Chowk, Kashmere Gate, Central Secretariat
- Chandni Chowk, New Delhi, Connaught Place
- Hauz Khas, Nehru Place, Dwarka Sector 21

---

## How to Run

### From project root:
```bash
python atlas/scripts/seed_db.py
```

### From backend directory:
```bash
cd atlas/backend
python -m app.scripts.seed_db
```

---

## What It Does

1. **Initializes tables** - Calls `init_db()` to ensure all tables exist
2. **Clears existing data** - Deletes all records from the 4 tables
3. **Seeds city boundary** - Inserts Delhi city polygon
4. **Seeds areas** - Creates 11 district boundaries
5. **Seeds pincodes** - Creates 30 pincode areas with boundaries
6. **Seeds points** - Creates 200 random POIs across 7 categories

---

## Data Characteristics

### Coordinates
- **Delhi Center:** (28.6139, 77.2090)
- **Points spread:** ±0.2 degrees (~22 km radius)
- **Area polygons:** 0.1 x 0.1 degree squares
- **Pincode polygons:** 0.04 x 0.04 degree squares

### Schema Compliance
All data matches the `DATABASE_SCHEMA.md` specification:
- **id** - INTEGER values (1, 2, 3...)
- **name** - VARCHAR strings
- **category** - VARCHAR (only for delhi_points)
- **geom** - GEOMETRY (POINT for points, POLYGON for areas/pincodes/city)

### Geometry Format
- Uses **WKT (Well-Known Text)** format
- Converted to GEOMETRY using `ST_GeomFromText()`
- Format: `POINT(lon lat)` or `POLYGON((lon lat, ...))`

---

## Sample Queries After Seeding

```sql
-- Count all points
SELECT COUNT(*) FROM delhi_points;
-- Expected: 200

-- List all areas
SELECT id, name FROM delhi_area;
-- Expected: 11 rows

-- Count points by category
SELECT category, COUNT(*) as count 
FROM delhi_points 
GROUP BY category 
ORDER BY count DESC;

-- Get points with coordinates
SELECT name, category, 
       ST_X(geom) as longitude, 
       ST_Y(geom) as latitude 
FROM delhi_points 
LIMIT 10;

-- List all pincodes
SELECT name FROM delhi_pincode ORDER BY name;
-- Expected: 110001 through 110030

-- Get city boundary
SELECT name, ST_AsText(geom) FROM delhi_city;
```

---

## Sample Chat Questions

After seeding, users can ask:

### Counts
- *"How many points are in the database?"* → 200
- *"How many areas are there?"* → 11
- *"Count points by category"*

### Lists
- *"Show me all restaurant names"*
- *"List all monuments in Delhi"*
- *"What are all the pincodes?"*

### Categories
- *"What categories of points exist?"*
- *"How many restaurants vs cafes?"*
- *"Show me all metro stations"*

### Geographic
- *"Show me points with their coordinates"*
- *"List all area names"*
- *"What's in the delhi_city table?"*

---

## Dependencies

```python
# Required packages
import random      # For generating random data
import duckdb      # Database connection
from shapely.geometry import Point, Polygon  # Geometry creation
from app.core.db import get_db_connection, init_db
```

Make sure these are installed:
```bash
pip install duckdb shapely
```

---

## Output Example

```
Database initialized successfully with Delhi schema.
Tables created: delhi_area, delhi_city, delhi_pincode, delhi_points
Seeding Delhi geographic data...
Seeding delhi_city...
Seeding delhi_area...
Seeding delhi_pincode...
Seeding delhi_points...
Seeding Complete!
  - 1 city boundary
  - 11 areas
  - 30 pincodes
  - 200 points of interest
```

---

## Notes

- **Random Generation:** POI locations are randomly scattered within Delhi bounds
- **Duplicate Names:** POI names may repeat (realistic - multiple Starbucks locations)
- **Boundaries:** Polygons are simplified approximations, not real boundaries
- **IDs:** Sequential integers starting from 1
- **No Primary Keys:** Schema allows nullable IDs as per DATABASE_SCHEMA.md

---

## Customization

To modify the seed data:

### Change number of points:
```python
point_count = 500  # Change from 200 to 500
```

### Add more areas:
```python
delhi_areas = [
    "Central Delhi",
    "Your New Area",
    # ... add more
]
```

### Add new POI categories:
```python
poi_categories = {
    "Restaurant": [...],
    "School": ["DPS", "Modern School", ...],  # New category
}
```

### Change Delhi boundary:
```python
city_boundary_coords = [
    (77.0, 28.4),
    # ... modify coordinates
]
```

---

**Ready to seed!** Run the script to populate your Delhi database. 🚀
