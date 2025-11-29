# Map Configuration Guide

## Map Tiles

Atlas.AI uses Latlong's vector tile service with Mapbox GL–compatible styles.

### Tile Style URL

```
https://tiles-v2.latlong.in/blue_essence.json
```

### Style JSON Structure

```json
{
  "version": 8,
  "name": "Blue Essence",
  "sources": {
    "latlong-vector": {
      "type": "vector",
      "tiles": [
        "https://tiles-v2.latlong.in/tiles/{z}/{x}/{y}.pbf"
      ],
      "minzoom": 0,
      "maxzoom": 14
    }
  },
  "sprite": "https://tiles-v2.latlong.in/sprite",
  "glyphs": "https://tiles-v2.latlong.in/fonts/{fontstack}/{range}.pbf",
  "layers": [...]
}
```

## Compatible Renderers

The style JSON requires a Mapbox GL–compatible renderer:

- **MapLibre GL JS** (used in Atlas.AI)
- **Mapbox GL JS**
- **Deck.gl**
- **Leaflet + mapbox-gl plugin**

Note: Traditional Leaflet `tileLayer` cannot use this JSON directly.

## Frontend Configuration

### Map Center

```javascript
// Delhi coordinates
const position = [28.6139, 77.2090];
```

### Zoom Level

```javascript
const defaultZoom = 13; // City-level view
```

### Integration with Leaflet

```javascript
import { MapContainer, TileLayer } from 'react-leaflet';
import 'maplibre-gl/dist/maplibre-gl.css';

// Using MapLibre GL with Leaflet
<MapContainer center={position} zoom={13}>
  <TileLayer
    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    attribution='&copy; OpenStreetMap contributors'
  />
</MapContainer>
```

## POI Color Coding

Each category has a distinct color for visual identification:

| Category | Color | Hex Code |
|----------|-------|----------|
| Restaurant | Red | `#EF4444` |
| Cafe | Amber | `#F59E0B` |
| Mall | Purple | `#8B5CF6` |
| Monument | Green | `#10B981` |
| Market | Pink | `#EC4899` |
| Hospital | Blue | `#3B82F6` |
| Metro Station | Orange | `#F97316` |
| Default | Gray | `#6B7280` |

### Color Mapping Implementation

```javascript
const getCategoryColor = (category) => {
  const colorMap = {
    'Restaurant': '#EF4444',
    'Cafe': '#F59E0B',
    'Mall': '#8B5CF6',
    'Monument': '#10B981',
    'Market': '#EC4899',
    'Hospital': '#3B82F6',
    'Metro Station': '#F97316',
    'default': '#6B7280'
  };
  return colorMap[category] || colorMap['default'];
};
```

### Marker Styling

```javascript
<CircleMarker
  center={[poi.lat, poi.lon]}
  pathOptions={{ 
    color: getCategoryColor(poi.category), 
    fillColor: getCategoryColor(poi.category), 
    fillOpacity: 0.7,
    weight: 2
  }}
  radius={6}
>
  <Popup>{poi.name}</Popup>
</CircleMarker>
```

## Layer Control

Toggle different data layers:

- **POIs/Competitors** - Show/hide point markers
- **Heatmap** - Density visualization
- **Areas** - District boundaries

## Heatmap Sample Data

```javascript
const heatmapData = [
  { lat: 28.6139, lon: 77.2090, intensity: 1.0 },  // Connaught Place
  { lat: 28.5244, lon: 77.1855, intensity: 0.9 },  // Hauz Khas
  { lat: 28.6692, lon: 77.4538, intensity: 0.8 },  // Noida
  { lat: 28.5355, lon: 77.3910, intensity: 0.7 },  // Nehru Place
];
```
