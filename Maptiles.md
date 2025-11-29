# Working with Latlong Map Tiles & Delhi Spatial Data

### *A Practical Guide to Using Latlong’s Vector Tile Style + GeoJSON Boundaries in Leaflet*

---

## 1. Introduction

Latlong provides a **Mapbox GL–compatible map style** rather than direct raster tiles.
Instead of PNG tiles, Latlong exposes a **Mapbox Style JSON** hosted at URLs like:

```
https://tiles-v2.latlong.in/blue_essence.json
```

This style JSON defines:

* Vector tile sources (`.pbf`)
* Tile server URLs
* Layer styling
* Sprites
* Fonts
* Zoom levels

Along with this, you also have **Delhi boundary geometry** (as GeoJSON or WKT multipolygon).

Combining these two allows you to:

* Render the complete India map
* Mask/clip the view to Delhi only
* Overlay business analytics, competitor density, POIs, etc.
* Build dashboards using Leaflet or Mapbox GL JS

This document explains how to do exactly that.

---

## 2. Understanding What `blue_essence.json` Provides

### It is a **Mapbox GL Style JSON**

This file is **not an image tile**.
It is a styling descriptor used by Mapbox GL–based renderers.

A typical structure looks like:

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

This tells your mapping library:

* where to fetch **vector tiles**
* how to **style** roads, labels, boundaries, landuse, etc.
* which **fonts and icons** to use

### **It requires a renderer that supports Mapbox GL styles**

Compatible renderers include:

* **Mapbox GL JS**
* **MapLibre GL JS**
* **Leaflet + mapbox-gl plugin**
* **Deck.gl**
* **OpenLayers (with vector tile support)**

Traditional Leaflet **tileLayer** cannot use this JSON directly.

---

## 3. Understanding Your Delhi Polygon Data

Your Delhi region is given as a **MULTIPOLYGON**, e.g.:

```
MULTIPOLYGON(((77.242... 28.66...), ...))
```

This geometry can be exported from DuckDB as **GeoJSON**, such as:

```sql
SELECT ST_AsGeoJSON(geometry) FROM delhi_boundaries;
```

This GeoJSON boundary is essential for:

* focusing the map on Delhi
* creating a masked/limited view
* overlaying demographic/business analysis
* performing spatial joins (competitors, hotspots, etc.)

---

## 4. Rendering Latlong’s Map Tiles in Leaflet

Since Latlong provides a **Mapbox GL style**, you must load it using Leaflet’s GL bridge:

### Install mapbox-gl-leaflet plugin (browser):

```html
<script src="https://unpkg.com/mapbox-gl@2.4.1/dist/mapbox-gl.js"></script>
<script src="https://unpkg.com/mapbox-gl-leaflet/leaflet-mapbox-gl.js"></script>
```

### Load the base map:

```js
var map = L.map("map", { zoomControl: true })
    .setView([28.6, 77.2], 10);

var glLayer = L.mapboxGL({
    style: "https://tiles-v2.latlong.in/blue_essence.json",
    accessToken: ""   // Optional if style does not require MB token
}).addTo(map);
```

This renders Latlong’s vector-tile based India map inside Leaflet.

---

## 5. Adding the Delhi Boundary Polygon

### Load your Delhi GeoJSON:

```js
const delhiBoundary = L.geoJSON(delhiGeoJSON, {
    style: {
        color: "red",
        weight: 2,
        fillOpacity: 0.1
    }
}).addTo(map);
```

### Fit the map to Delhi:

```js
map.fitBounds(delhiBoundary.getBounds());
```

---

## 6. Clipping the Map to Only Show Delhi (Masking Technique)

Leaflet cannot “clip” a tile layer directly, but you can mask the rest of the country using a polygon with a hole.

### Create a world-extent polygon with a Delhi-shaped hole:

```js
const world = [
  [-180, -90], [180, -90], [180, 90], [-180, 90]
];

const delhiPolygon = delhiGeoJSON.features[0].geometry.coordinates[0];

const mask = {
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      world,         // outer ring
      delhiPolygon   // inner hole
    ]
  }
};

L.geoJSON(mask, {
    style: {
      color: "#000",
      fillColor: "#000",
      fillOpacity: 0.55,
      stroke: false
    }
}).addTo(map);
```

This darkens everything *outside* Delhi while preserving full interactivity and styling inside.

---

## 7. Adding Business, Competitor, and Landmark Data

You can use Latlong’s Location APIs to fetch:

* landmarks
* POIs
* competition
* distances
* desirability metrics

Example (Python):

```python
import requests

headers = {"X-Authorization-Token": LATLONG_TOKEN}

res = requests.get(
    "https://apihub.latlong.ai/v4/landmarks.json",
    headers=headers,
    params={"lat": 28.6337, "lon": 77.1164}
)
```

Add them to Leaflet:

```js
L.marker([lat, lon]).addTo(map).bindPopup("Competitor shop");
```

Or cluster them:

```js
L.markerClusterGroup().addLayer(marker);
```

---

## 8. Optional: Heatmaps, Choropleths, and Spatial Analytics

Once Delhi is loaded:

* Divide area into grids (H3, S2, or your own)
* Summarize:

  * number of competitors
  * footfall estimates
  * accessibility metrics
  * nearby landmarks
  * business density
* Render as:

  * heatmaps (`leaflet-heat`)
  * choropleth layers
  * hexbin maps

Example:

```js
L.heatLayer([
  [lat, lon, intensity]
], { radius: 25 }).addTo(map);
```

---

## 9. Summary

| Component                                    | Purpose            | How It Works                                     |
| -------------------------------------------- | ------------------ | ------------------------------------------------ |
| **Latlong Style JSON (`blue_essence.json`)** | Base India map     | Mapbox GL style: vector tile source + styling    |
| **Delhi Multipolygon**                       | Region of interest | Extracted from GeoJSON, used to clip and overlay |
| **Leaflet + MapboxGL plugin**                | Map rendering      | Displays Latlong’s style inside Leaflet          |
| **Masking Technique**                        | Show only Delhi    | Polygon hole mask darkens rest of India          |
| **Latlong APIs**                             | POIs / landmarks   | Add business intelligence layers                 |
| **Custom layers**                            | Heatmaps, grids    | Visual analytics on Delhi region                 |

---

## 10. What This Enables for Your Hackathon Project

* A clean, custom Delhi-only map
* Ability to score locations by desirability
* Overlay competitor POIs
* Study spatial clustering of businesses
* Build dashboards for “ideal shop placement”
* Combine your DuckDB spatial data with Leaflet display
* Do routing, heatmaps, grid scoring, walkability, etc.
