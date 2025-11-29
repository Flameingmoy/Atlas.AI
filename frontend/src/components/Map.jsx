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

// Color mapping for POI categories (case-insensitive with keyword matching)
const getCategoryColor = (category) => {
    if (!category) return '#6B7280'; // default gray
    
    const cat = category.toLowerCase();
    
    // Food & Dining - Red tones
    if (cat.includes('restaurant') || cat.includes('diner') || cat.includes('steakhouse') || 
        cat.includes('buffet') || cat.includes('barbecue') || cat.includes('grill')) {
        return '#EF4444'; // Red
    }
    
    // Cafes & Coffee - Amber/Orange
    if (cat.includes('cafe') || cat.includes('coffee') || cat.includes('tea') || 
        cat.includes('bakery') || cat.includes('patisserie') || cat.includes('dessert')) {
        return '#F59E0B'; // Amber
    }
    
    // Shopping & Malls - Purple
    if (cat.includes('mall') || cat.includes('shopping') || cat.includes('store') || 
        cat.includes('shop') || cat.includes('retail') || cat.includes('market') ||
        cat.includes('supermarket') || cat.includes('grocery')) {
        return '#8B5CF6'; // Purple
    }
    
    // Monuments & Landmarks - Green
    if (cat.includes('monument') || cat.includes('landmark') || cat.includes('fort') ||
        cat.includes('palace') || cat.includes('temple') || cat.includes('mosque') ||
        cat.includes('church') || cat.includes('museum') || cat.includes('heritage') ||
        cat.includes('historical')) {
        return '#10B981'; // Green
    }
    
    // Healthcare - Blue
    if (cat.includes('hospital') || cat.includes('clinic') || cat.includes('medical') ||
        cat.includes('pharmacy') || cat.includes('doctor') || cat.includes('dentist') ||
        cat.includes('health')) {
        return '#3B82F6'; // Blue
    }
    
    // Transport - Orange
    if (cat.includes('metro') || cat.includes('station') || cat.includes('railway') ||
        cat.includes('train') || cat.includes('bus') || cat.includes('transport')) {
        return '#F97316'; // Orange
    }
    
    // Entertainment & Leisure - Pink
    if (cat.includes('cinema') || cat.includes('theatre') || cat.includes('theater') ||
        cat.includes('park') || cat.includes('entertainment') || cat.includes('amusement') ||
        cat.includes('gym') || cat.includes('spa') || cat.includes('club')) {
        return '#EC4899'; // Pink
    }
    
    // Education - Cyan
    if (cat.includes('school') || cat.includes('college') || cat.includes('university') ||
        cat.includes('education') || cat.includes('library')) {
        return '#06B6D4'; // Cyan
    }
    
    // Hotels & Accommodation - Indigo
    if (cat.includes('hotel') || cat.includes('resort') || cat.includes('hostel') ||
        cat.includes('lodge') || cat.includes('motel')) {
        return '#6366F1'; // Indigo
    }
    
    // Default
    return '#6B7280'; // Gray
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

        // Add POI markers - filter to Delhi radius and limit count
        if (activeLayers.includes('competitors')) {
            const latRad = DELHI_CENTER[1] * (Math.PI / 180);
            const kmPerDegLat = 111.32;
            const kmPerDegLng = 111.32 * Math.cos(latRad);
            
            // Filter POIs to only those within Delhi circle
            const filteredPois = pois.filter(poi => {
                if (!poi.lat || !poi.lon) return false;
                const dLat = (poi.lat - DELHI_CENTER[1]) * kmPerDegLat;
                const dLng = (poi.lon - DELHI_CENTER[0]) * kmPerDegLng;
                const distKm = Math.sqrt(dLat * dLat + dLng * dLng);
                return distKm <= RADIUS_KM;
            }).slice(0, 300); // Limit to 300 markers max for performance

            filteredPois.forEach((poi) => {
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
            });
            
            console.log(`Rendered ${filteredPois.length} markers (from ${pois.length} total)`);
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
                    fontSize: '11px',
                    boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
                    zIndex: 1,
                    maxHeight: '300px',
                    overflowY: 'auto'
                }}>
                    <h4 style={{ fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>Categories</h4>
                    {[
                        { name: 'Restaurants', color: '#EF4444' },
                        { name: 'Cafes & Bakeries', color: '#F59E0B' },
                        { name: 'Shopping & Markets', color: '#8B5CF6' },
                        { name: 'Monuments & Landmarks', color: '#10B981' },
                        { name: 'Healthcare', color: '#3B82F6' },
                        { name: 'Transport', color: '#F97316' },
                        { name: 'Entertainment', color: '#EC4899' },
                        { name: 'Education', color: '#06B6D4' },
                        { name: 'Hotels', color: '#6366F1' },
                        { name: 'Other', color: '#6B7280' }
                    ].map(cat => (
                        <div key={cat.name} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: cat.color, flexShrink: 0 }}></div>
                            <span style={{ color: '#555' }}>{cat.name}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Map;
