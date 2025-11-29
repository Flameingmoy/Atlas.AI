# Database Schema Documentation

This document describes the database schemas for the Delhi geographic data tables.

## Tables Overview

The database contains four main tables for storing geographic data about Delhi:
- `delhi_area` - Area/district boundaries
- `delhi_city` - City boundaries
- `delhi_pincode` - Pincode/postal code boundaries
- `delhi_points` - Points of interest

---

## delhi_area

Stores geographic boundaries for areas/districts in Delhi.

| Column Name | Data Type | Nullable | Key | Default | Extra |
|-------------|-----------|----------|-----|---------|-------|
| id          | INTEGER   | YES      | NULL | NULL    | NULL  |
| name        | VARCHAR   | YES      | NULL | NULL    | NULL  |
| geom        | GEOMETRY  | YES      | NULL | NULL    | NULL  |

**Description:**
- `id` - Unique identifier for each area
- `name` - Name of the area/district
- `geom` - Geometric representation of the area boundary

---

## delhi_city

Stores geographic boundaries for the city of Delhi.

| Column Name | Data Type | Nullable | Key | Default | Extra |
|-------------|-----------|----------|-----|---------|-------|
| id          | INTEGER   | YES      | NULL | NULL    | NULL  |
| name        | VARCHAR   | YES      | NULL | NULL    | NULL  |
| geom        | GEOMETRY  | YES      | NULL | NULL    | NULL  |

**Description:**
- `id` - Unique identifier for the city boundary
- `name` - Name of the city
- `geom` - Geometric representation of the city boundary

---

## delhi_pincode

Stores geographic boundaries for pincode/postal code areas in Delhi.

| Column Name | Data Type | Nullable | Key | Default | Extra |
|-------------|-----------|----------|-----|---------|-------|
| id          | INTEGER   | YES      | NULL | NULL    | NULL  |
| name        | VARCHAR   | YES      | NULL | NULL    | NULL  |
| geom        | GEOMETRY  | YES      | NULL | NULL    | NULL  |

**Description:**
- `id` - Unique identifier for each pincode area
- `name` - Pincode/postal code value
- `geom` - Geometric representation of the pincode boundary

---

## delhi_points

Stores point locations for various points of interest in Delhi.

| Column Name | Data Type | Nullable | Key | Default | Extra |
|-------------|-----------|----------|-----|---------|-------|
| id          | INTEGER   | YES      | NULL | NULL    | NULL  |
| name        | VARCHAR   | YES      | NULL | NULL    | NULL  |
| category    | VARCHAR   | YES      | NULL | NULL    | NULL  |
| geom        | GEOMETRY  | YES      | NULL | NULL    | NULL  |

**Description:**
- `id` - Unique identifier for each point
- `name` - Name of the point of interest
- `category` - Category/type of the point of interest
- `geom` - Geometric representation of the point location (point geometry)

---

## Notes

- All tables use the `GEOMETRY` data type for spatial data, which supports various geometric types (POINT, POLYGON, MULTIPOLYGON, etc.)
- The `geom` column stores the actual geographic coordinates and shapes
- All columns are nullable, allowing for flexible data insertion
- No primary keys or constraints are explicitly defined in the current schema
