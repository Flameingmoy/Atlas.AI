import React, { useEffect, useState, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { fetchPOIs } from '../services/api';

// Delhi center and radius
const DELHI_CENTER = [77.1025, 28.6139]; // [lng, lat]
const RADIUS_KM = 35;

// Generate circle coordinates
const generateCircle = (center, radiusKm, steps = 64) => {
    const coords = [];
    const latRad = center[1] * (Math.PI / 180);
    const kmPerDegLat = 111.32;
    const kmPerDegLng = 111.32 * Math.cos(latRad);
    
    for (let i = 0; i <= steps; i++) {
        const angle = (i / steps) * 2 * Math.PI;
        const lng = center[0] + (radiusKm / kmPerDegLng) * Math.cos(angle);
        const lat = center[1] + (radiusKm / kmPerDegLat) * Math.sin(angle);
        coords.push([lng, lat]);
    }
    return coords;
};

const DELHI_BOUNDARY = generateCircle(DELHI_CENTER, RADIUS_KM);
const WORLD_BOUNDS = [[-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]];

// Color mapping for POI categories
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

const Map = ({ activeLayers }) => {
    const mapContainer = useRef(null);
    const map = useRef(null);
    const markersRef = useRef([]);
    const [pois, setPois] = useState([]);
    const [mapLoaded, setMapLoaded] = useState(false);

    // Initialize MapLibre GL map with Latlong tiles
    useEffect(() => {
        if (map.current) return;

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: 'https://tiles-v2.latlong.in/blue_essence.json',
            center: DELHI_CENTER,
            zoom: 10,
            minZoom: 9,
            maxZoom: 15,
            maxBounds: [[76.5, 28.0], [77.7, 29.2]]
        });

        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

        map.current.on('load', () => {
            console.log('Latlong map loaded');
            
            // Add Delhi mask layer
            map.current.addSource('delhi-mask', {
                type: 'geojson',
                data: {
                    type: 'Feature',
                    geometry: {
                        type: 'Polygon',
                        coordinates: [WORLD_BOUNDS, DELHI_BOUNDARY]
                    }
                }
            });

            map.current.addLayer({
                id: 'delhi-mask-layer',
                type: 'fill',
                source: 'delhi-mask',
                paint: {
                    'fill-color': '#000000',
                    'fill-opacity': 0.8
                }
            });

            // Add Delhi boundary outline
            map.current.addSource('delhi-boundary', {
                type: 'geojson',
                data: {
                    type: 'Feature',
                    geometry: {
                        type: 'LineString',
                        coordinates: DELHI_BOUNDARY
                    }
                }
            });

            map.current.addLayer({
                id: 'delhi-boundary-line',
                type: 'line',
                source: 'delhi-boundary',
                paint: {
                    'line-color': '#3B82F6',
                    'line-width': 2
                }
            });

            setMapLoaded(true);
        });

        map.current.on('error', (e) => {
            // Suppress known tile errors
            if (e.error) {
                const msg = e.error.message || '';
                if (msg.includes('Source layer') || msg.includes('403') || msg.includes('AJAXError')) {
                    return;
                }
            }
        });

        return () => {
            if (map.current) {
                map.current.remove();
                map.current = null;
            }
        };
    }, []);

    // Load POIs
    useEffect(() => {
        if (activeLayers.includes('competitors')) {
            fetchPOIs().then(data => {
                if (data) setPois(data);
            });
        } else {
            setPois([]);
        }
    }, [activeLayers]);

    // Add/remove markers
    useEffect(() => {
        if (!map.current || !mapLoaded) return;

        // Clear existing markers
        markersRef.current.forEach(m => m.remove());
        markersRef.current = [];

        // Add POI markers
        if (activeLayers.includes('competitors')) {
            pois.forEach((poi) => {
                if (poi.lat && poi.lon) {
                    const color = getCategoryColor(poi.category);
                    
                    const el = document.createElement('div');
                    el.style.width = '12px';
                    el.style.height = '12px';
                    el.style.backgroundColor = color;
                    el.style.borderRadius = '50%';
                    el.style.border = '2px solid white';
                    el.style.cursor = 'pointer';

                    const marker = new maplibregl.Marker({ element: el })
                        .setLngLat([poi.lon, poi.lat])
                        .setPopup(
                            new maplibregl.Popup({ offset: 25 })
                                .setHTML(`<div style="color:#333;"><b>${poi.name}</b><br/>${poi.category || ''}</div>`)
                        )
                        .addTo(map.current);

                    markersRef.current.push(marker);
                }
            });
        }
    }, [pois, activeLayers, mapLoaded]);

    return (
        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
            <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
            
            {activeLayers.includes('competitors') && (
                <div style={{
                    position: 'absolute',
                    bottom: '80px',
                    right: '10px',
                    background: 'rgba(255,255,255,0.95)',
                    borderRadius: '8px',
                    padding: '12px',
                    fontSize: '12px',
                    boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
                    zIndex: 1
                }}>
                    <h4 style={{ fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>Categories</h4>
                    {['Restaurant', 'Cafe', 'Mall', 'Monument', 'Market', 'Hospital', 'Metro Station'].map(cat => (
                        <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: getCategoryColor(cat) }}></div>
                            <span style={{ color: '#555' }}>{cat}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Map;
