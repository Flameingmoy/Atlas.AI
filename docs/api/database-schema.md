# Database Schema Reference

## Overview

Atlas.AI uses DuckDB with spatial extensions for storing and querying Delhi geographic data.

## Tables

### delhi_city

City boundary polygon for Delhi NCT.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| name | VARCHAR | City name |
| geom | GEOMETRY | City boundary polygon |

**Sample Query:**
```sql
SELECT id, name, ST_AsText(geom) FROM delhi_city;
```

---

### delhi_area

Administrative areas/districts within Delhi.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| name | VARCHAR | Area/district name |
| geom | GEOMETRY | Area boundary polygon |

**Areas Included:**
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

**Sample Query:**
```sql
SELECT id, name FROM delhi_area ORDER BY name;
```

---

### delhi_pincode

Postal code boundaries.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| name | VARCHAR | Pincode (110001-110030) |
| geom | GEOMETRY | Pincode boundary polygon |

**Sample Query:**
```sql
SELECT name, ST_Area(geom) as area FROM delhi_pincode;
```

---

### delhi_points

Points of interest across Delhi.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| name | VARCHAR | POI name |
| category | VARCHAR | POI category |
| geom | GEOMETRY | Point location |

**Categories:**
- Restaurant
- Cafe
- Mall
- Monument
- Market
- Hospital
- Metro Station

**Sample Queries:**

```sql
-- Get all restaurants
SELECT id, name, ST_Y(geom) as lat, ST_X(geom) as lon 
FROM delhi_points 
WHERE category = 'Restaurant';

-- Count POIs by category
SELECT category, COUNT(*) as count 
FROM delhi_points 
GROUP BY category 
ORDER BY count DESC;

-- Find POIs by name pattern
SELECT * FROM delhi_points 
WHERE name ILIKE '%coffee%';
```

---

## Spatial Functions

### Common Operations

| Function | Description | Example |
|----------|-------------|---------|
| `ST_X(geom)` | Get longitude | `SELECT ST_X(geom) FROM delhi_points` |
| `ST_Y(geom)` | Get latitude | `SELECT ST_Y(geom) FROM delhi_points` |
| `ST_Point(lon, lat)` | Create point | `ST_Point(77.2090, 28.6139)` |
| `ST_AsText(geom)` | Geometry as WKT | `SELECT ST_AsText(geom) FROM delhi_city` |
| `ST_AsGeoJSON(geom)` | Geometry as GeoJSON | `SELECT ST_AsGeoJSON(geom) FROM delhi_area` |
| `ST_SetSRID(geom, 4326)` | Set coordinate system | Standard for lat/lon |

### Coordinate Reference

All geometries use **EPSG:4326** (WGS 84):
- Latitude: ~28.4 to ~28.9 (Delhi range)
- Longitude: ~77.0 to ~77.4 (Delhi range)

---

## Database Connection

### Python (DuckDB)

```python
import duckdb

conn = duckdb.connect('data/atlas.duckdb')
conn.execute("INSTALL spatial; LOAD spatial;")

# Query example
result = conn.execute("""
    SELECT name, category, ST_Y(geom) as lat, ST_X(geom) as lon
    FROM delhi_points
    WHERE category = 'Restaurant'
    LIMIT 10
""").fetchdf()
```

### Environment Variables

```env
DATABASE_PATH=data/atlas.duckdb
```
