# Database Seeding Guide

## Overview

The seed script (`scripts/seed_db.py`) populates the DuckDB database with sample Delhi geographic data.

## What Gets Seeded

### delhi_city (1 record)

- Delhi NCT boundary polygon
- Coverage: 77.0-77.4 longitude, 28.4-28.9 latitude

### delhi_area (11 areas)

Administrative districts:
1. Central Delhi
2. North Delhi
3. South Delhi
4. East Delhi
5. West Delhi
6. New Delhi
7. North West Delhi
8. North East Delhi
9. South West Delhi
10. South East Delhi
11. Shahdara

### delhi_pincode (30 records)

Pincodes from 110001 to 110030, each with boundary polygons.

### delhi_points (200+ POIs)

Points of interest across 7 categories:

| Category | Sample Names |
|----------|--------------|
| **Restaurant** | Karim's, Bukhara, Indian Accent, Moti Mahal, Paranthe Wali Gali, Saravana Bhavan, Haldiram's, Bikanervala |
| **Cafe** | Starbucks, Cafe Coffee Day, Blue Tokai Coffee, Indian Coffee House, Café Turtle, Chai Point |
| **Mall** | Select Citywalk, DLF Promenade, Ambience Mall, Pacific Mall, Vegas Mall, DLF Mall of India |
| **Monument** | Red Fort, Qutub Minar, India Gate, Humayun's Tomb, Lotus Temple, Akshardham Temple, Jama Masjid |
| **Market** | Chandni Chowk, Sarojini Nagar, Lajpat Nagar, Connaught Place, Khan Market, Dilli Haat |
| **Hospital** | AIIMS, Safdarjung Hospital, Apollo Hospital, Max Hospital, Fortis Hospital, Medanta |
| **Metro Station** | Rajiv Chowk, Kashmere Gate, Central Secretariat, New Delhi, Hauz Khas, Dwarka Sector 21 |

## Running the Seed Script

### From project root:

```bash
python scripts/seed_db.py
```

### With custom database path:

```bash
DATABASE_PATH=/path/to/custom.duckdb python scripts/seed_db.py
```

## Seed Process

1. **Initialize tables** - Creates schema if not exists
2. **Clear existing data** - Deletes all records from tables
3. **Seed city boundary** - Inserts Delhi city polygon
4. **Seed areas** - Creates 11 district boundaries
5. **Seed pincodes** - Creates 30 pincode area polygons
6. **Seed points** - Creates 200+ random POIs

## Customization

### Adding More POIs

Edit the POI names in `scripts/seed_db.py`:

```python
POI_NAMES = {
    "Restaurant": ["Karim's", "Bukhara", ...],
    "YourCategory": ["Name1", "Name2", ...],
}
```

### Changing Boundaries

Modify the Delhi boundary coordinates in the seed script:

```python
DELHI_BOUNDS = {
    "min_lat": 28.4,
    "max_lat": 28.9,
    "min_lon": 77.0,
    "max_lon": 77.4
}
```

## Verification

After seeding, verify data:

```bash
python -c "
import duckdb
conn = duckdb.connect('data/atlas.duckdb')
print('City:', conn.execute('SELECT COUNT(*) FROM delhi_city').fetchone()[0])
print('Areas:', conn.execute('SELECT COUNT(*) FROM delhi_area').fetchone()[0])
print('Pincodes:', conn.execute('SELECT COUNT(*) FROM delhi_pincode').fetchone()[0])
print('Points:', conn.execute('SELECT COUNT(*) FROM delhi_points').fetchone()[0])
"
```

Expected output:
```
City: 1
Areas: 11
Pincodes: 30
Points: 200
```
