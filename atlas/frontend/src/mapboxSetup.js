// Setup MapLibre GL globally for the leaflet plugin
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// mapbox-gl-leaflet looks for window.mapboxgl
window.mapboxgl = maplibregl;

// Now import the leaflet plugin
import 'mapbox-gl-leaflet';

export default maplibregl;
