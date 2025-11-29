# Migration Notes

## Delhi Schema Migration (Nov 2025)

### Overview

Migrated from Bangalore POIs schema to Delhi Geographic schema.

### Schema Changes

| Old (Bangalore) | New (Delhi) |
|-----------------|-------------|
| `pois` table | `delhi_points` table |
| `demographics` table | Removed |
| UUID primary keys | INTEGER primary keys |
| `location` column | `geom` column |
| `subcategory` column | Removed |
| `metadata_json` column | Removed |
| H3 indexing | Removed |

### New Tables Added

- `delhi_city` - City boundary
- `delhi_area` - District boundaries
- `delhi_pincode` - Postal code boundaries

### API Changes

| Old Endpoint | New Endpoint |
|--------------|--------------|
| `GET /pois` | `GET /points` |
| - | `GET /areas` (new) |
| - | `GET /pincodes` (new) |

### Function Renames

| Old | New |
|-----|-----|
| `fetchPOIs()` | `fetchPoints()` |
| `get_bangalore_demographics()` | `get_delhi_info()` |

### Coordinate Changes

```javascript
// Old (Bangalore)
const position = [12.9716, 77.5946];

// New (Delhi)  
const position = [28.6139, 77.2090];
```

### Files Modified

- `backend/app/core/db.py` - Schema definitions
- `backend/app/api/routes.py` - Endpoints
- `backend/app/services/ai_agent.py` - Tools and prompts
- `backend/app/services/text_to_sql_service.py` - Schema context
- `frontend/src/services/api.js` - API client
- `frontend/src/components/Map.jsx` - Coordinates
- `frontend/src/App.jsx` - UI text
