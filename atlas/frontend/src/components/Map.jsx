import React, { useEffect, useState, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { fetchPOIs } from '../services/api';

// Delhi NCT approximate boundary coordinates [lng, lat]
const DELHI_BOUNDARY = [
    [76.8388, 28.8845], [76.8686, 28.8739], [76.9063, 28.8804], [76.9348, 28.8687],
    [76.9580, 28.8476], [76.9855, 28.8395], [77.0207, 28.8433], [77.0568, 28.8331],
    [77.0924, 28.8121], [77.1172, 28.7918], [77.1458, 28.7726], [77.1680, 28.7594],
    [77.2002, 28.7669], [77.2279, 28.7640], [77.2553, 28.7521], [77.2845, 28.7295],
    [77.3087, 28.7072], [77.3348, 28.6838], [77.3499, 28.6515], [77.3470, 28.6155],
    [77.3391, 28.5845], [77.3262, 28.5521], [77.3128, 28.5224], [77.2933, 28.4962],
    [77.2683, 28.4789], [77.2380, 28.4706], [77.2048, 28.4681], [77.1709, 28.4734],
    [77.1387, 28.4841], [77.1080, 28.4998], [77.0788, 28.5194], [77.0516, 28.5421],
    [77.0268, 28.5672], [77.0047, 28.5943], [76.9852, 28.6228], [76.9687, 28.6527],
    [76.9552, 28.6841], [76.9449, 28.7167], [76.9378, 28.7503], [76.9340, 28.7845],
    [76.9200, 28.8100], [76.8900, 28.8350], [76.8600, 28.8600], [76.8388, 28.8845]
];

// World coordinates for mask (covers everything outside Delhi)
const WORLD_BOUNDS = [
    [-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]
];

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

    // Initialize MapLibre GL map
    useEffect(() => {
        if (map.current) return;

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: 'https://tiles-v2.latlong.in/blue_essence.json',
            center: [77.1025, 28.6139], // Delhi center [lng, lat]
            zoom: 10,
            minZoom: 9,
            maxZoom: 18,
            maxBounds: [[76.7, 28.35], [77.5, 28.95]] // Restrict to Delhi area
        });

        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

        map.current.on('load', () => {
            console.log('Map loaded successfully');
            
            // Add Delhi mask layer - darkens everything outside Delhi
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
                    'fill-opacity': 0.7
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
                    'line-width': 2,
                    'line-opacity': 0.8
                }
            });

            setMapLoaded(true);
        });

        map.current.on('error', (e) => {
            // Only log actual errors, not tile loading issues
            if (e.error && e.error.message) {
                console.error('Map error:', e.error.message);
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
        const loadData = async () => {
            const data = await fetchPOIs();
            setPois(data);
        };
        loadData();
    }, []);

    // Add/remove markers based on activeLayers
    useEffect(() => {
        if (!map.current || !mapLoaded) return;

        // Clear existing markers
        markersRef.current.forEach(marker => marker.remove());
        markersRef.current = [];

        // Add POI markers if competitors layer is active
        if (activeLayers.includes('competitors')) {
            pois.forEach((poi) => {
                if (poi.lat && poi.lon) {
                    const color = getCategoryColor(poi.category);
                    
                    // Create marker element
                    const el = document.createElement('div');
                    el.className = 'poi-marker';
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
                                .setHTML(`
                                    <div style="color: #333;">
                                        <strong>${poi.name}</strong><br/>
                                        <span style="font-size: 12px;">Category: ${poi.category || 'Unknown'}</span>
                                    </div>
                                `)
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
            
            {/* Category Legend */}
            {activeLayers.includes('competitors') && (
                <div style={{
                    position: 'absolute',
                    bottom: '80px',
                    right: '10px',
                    background: 'rgba(255,255,255,0.95)',
                    backdropFilter: 'blur(4px)',
                    borderRadius: '8px',
                    padding: '12px',
                    fontSize: '12px',
                    boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
                    zIndex: 1
                }}>
                    <h4 style={{ fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>Categories</h4>
                    {['Restaurant', 'Cafe', 'Mall', 'Monument', 'Market', 'Hospital', 'Metro Station'].map(cat => (
                        <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <div style={{ 
                                width: '12px', 
                                height: '12px', 
                                borderRadius: '50%', 
                                backgroundColor: getCategoryColor(cat) 
                            }}></div>
                            <span style={{ color: '#555' }}>{cat}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Map;
