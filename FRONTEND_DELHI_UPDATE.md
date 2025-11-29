# Frontend Updates for Delhi Schema

## Overview

Updated the frontend to work with the new Delhi geographic schema and API endpoints.

---

## Files Modified

### ✅ 1. `atlas/frontend/src/services/api.js`

**Changes:**
- Updated endpoint: `/pois` → `/points`
- Renamed function: `fetchPOIs()` → `fetchPoints()`
- Added backward compatibility alias for `fetchPOIs`

**Before:**
```javascript
const response = await axios.get(`${API_URL}/pois`, { params: { category } });
```

**After:**
```javascript
const response = await axios.get(`${API_URL}/points`, { params: { category } });
```

---

### ✅ 2. `atlas/frontend/src/components/Map.jsx`

**Changes:**
- Updated coordinates: Bangalore → Delhi
- Updated heatmap sample data for Delhi locations

**Coordinate Changes:**
```javascript
// Before (Bangalore)
const position = [12.9716, 77.5946];

// After (Delhi)
const position = [28.6139, 77.2090];
```

**Heatmap Sample Data:**
```javascript
// Before
{ lat: 12.9716, lon: 77.5946, intensity: 1.0 }, // MG Road
{ lat: 12.9352, lon: 77.6245, intensity: 0.9 }, // Koramangala

// After
{ lat: 28.6139, lon: 77.2090, intensity: 1.0 }, // Connaught Place
{ lat: 28.5244, lon: 77.1855, intensity: 0.9 }, // Hauz Khas
{ lat: 28.6692, lon: 77.4538, intensity: 0.8 }, // Noida
{ lat: 28.5355, lon: 77.3910, intensity: 0.7 }, // Nehru Place
```

---

### ✅ 3. `atlas/frontend/src/App.jsx`

**Changes:**
- Updated chat placeholder text to reflect Delhi data

**Before:**
```javascript
placeholder="Ask Atlas: 'Show me high foot traffic areas...'"
```

**After:**
```javascript
placeholder="Ask Atlas: 'Show me all restaurants in Delhi' or 'What areas exist?'"
```

---

## API Endpoint Changes

| Old Endpoint | New Endpoint | Description |
|--------------|--------------|-------------|
| `GET /api/v1/pois` | `GET /api/v1/points` | Get points of interest |
| - | `GET /api/v1/areas` | Get Delhi areas (NEW) |
| - | `GET /api/v1/pincodes` | Get pincodes (NEW) |

---

## Map Configuration

### Center Coordinates

**Bangalore (Old):**
- Latitude: 12.9716
- Longitude: 77.5946

**Delhi (New):**
- Latitude: 28.6139
- Longitude: 77.2090

### Default Zoom
- Remains at **13** (city-level view)

---

## Testing the Frontend

### 1. Check Map Loads Correctly
- Map should center on Delhi
- Points should load from `/api/v1/points`

### 2. Test Chat Queries
Try these questions:
- *"How many points are in the database?"*
- *"Show me all restaurants"*
- *"What categories exist?"*
- *"List all areas in Delhi"*

### 3. Test Map Layers
- Toggle "competitors" layer → should show delhi_points
- Toggle "heatmap" layer → should show Delhi heatmap points

---

## Backward Compatibility

The `fetchPOIs` function is still available as an alias to `fetchPoints`, so any existing code calling `fetchPOIs()` will still work.

```javascript
// Both work
const points = await fetchPoints();
const points = await fetchPOIs(); // Alias to fetchPoints
```

---

## Data Structure

The points data structure remains the same:

```javascript
{
  "id": 1,              // INTEGER (not UUID anymore)
  "name": "Karim's",
  "category": "Restaurant",
  "lat": 28.6139,
  "lon": 77.2090
}
```

**Key Changes:**
- `id` is now INTEGER instead of UUID string
- No `subcategory` field
- No `metadata_json` field

---

## Sample Questions for Users

Update your UI or documentation with these Delhi-specific examples:

### Category Queries:
- *"Show me all monuments"*
- *"List all metro stations"*
- *"How many restaurants are there?"*

### Area Queries:
- *"What areas exist in Delhi?"*
- *"Show me all district names"*

### Pincode Queries:
- *"List all pincodes"*
- *"How many pincode areas are there?"*

### Location Queries:
- *"Show me points near Connaught Place"*
- *"What's in Hauz Khas?"*

---

## Known Issues / Limitations

1. **Mock Heatmap Data** - The heatmap layer uses hardcoded sample points, not real data
2. **Layer Names** - Still uses "competitors" and "heatmap" - could be renamed to "points" and "density"
3. **No Area Boundaries** - Map doesn't display area/pincode polygons yet

---

## Future Enhancements

### Recommended Improvements:

1. **Display Area Boundaries**
   - Add polygon layers for delhi_area and delhi_pincode
   - Show boundaries on map with hover labels

2. **Update Layer Names**
   ```javascript
   // Current
   ['competitors', 'heatmap']
   
   // Suggested
   ['points', 'areas', 'pincodes', 'heatmap']
   ```

3. **Add New Endpoints to Frontend**
   ```javascript
   export const fetchAreas = async () => {
       const response = await axios.get(`${API_URL}/areas`);
       return response.data;
   };
   
   export const fetchPincodes = async () => {
       const response = await axios.get(`${API_URL}/pincodes`);
       return response.data;
   };
   ```

4. **Category Filtering**
   - Add dropdown to filter points by category
   - Use the `category` parameter: `/points?category=Restaurant`

5. **Real Heatmap**
   - Replace mock heatmap with actual density calculation
   - Use leaflet-heat plugin for proper heatmap rendering

---

## Restart Instructions

After these changes, restart your frontend dev server:

```bash
cd atlas/frontend
npm run dev
```

The map should now:
✅ Center on Delhi (28.6139, 77.2090)  
✅ Load points from `/api/v1/points`  
✅ Display Delhi POIs (restaurants, monuments, etc.)  
✅ Work with text-to-SQL chat queries  

---

**Frontend migration complete!** 🎉

Your Atlas AI frontend now works with the Delhi geographic database.
