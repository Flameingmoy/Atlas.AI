import React, { useEffect, useState, useRef, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { fetchPointsViewport, fetchReverseGeocode, fetchIsochrone, fetchLandmarks } from '../services/api';

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

const Map = ({ activeLayers, selectedLocation, mapCenter, filteredPOIs }) => {
    const mapContainer = useRef(null);
    const map = useRef(null);
    const markersRef = useRef([]);
    const selectedMarkerRef = useRef(null);
    const isochroneSourceRef = useRef(false);
    const [pois, setPois] = useState([]);
    const [mapLoaded, setMapLoaded] = useState(false);
    const fetchTimeoutRef = useRef(null);
    const [clickedLocation, setClickedLocation] = useState(null);
    const [isLoadingAddress, setIsLoadingAddress] = useState(false);
    const [showIsochrone, setShowIsochrone] = useState(false);
    const [isochroneDistance, setIsochroneDistance] = useState(1.0);

    // Initialize MapLibre GL map with Latlong tiles
    useEffect(() => {
        if (map.current) return;

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: 'https://tiles-v2.latlong.in/blue_essence.json',
            center: DELHI_CENTER,
            zoom: 10,
            minZoom: 9,
            maxZoom: 18,
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

            // Add isochrone source and layer (initially empty)
            map.current.addSource('isochrone', {
                type: 'geojson',
                data: {
                    type: 'FeatureCollection',
                    features: []
                }
            });

            map.current.addLayer({
                id: 'isochrone-fill',
                type: 'fill',
                source: 'isochrone',
                paint: {
                    'fill-color': '#3B82F6',
                    'fill-opacity': 0.2
                }
            });

            map.current.addLayer({
                id: 'isochrone-outline',
                type: 'line',
                source: 'isochrone',
                paint: {
                    'line-color': '#3B82F6',
                    'line-width': 2
                }
            });

            isochroneSourceRef.current = true;
            setMapLoaded(true);
        });

        // Handle map click for reverse geocoding
        map.current.on('click', async (e) => {
            const { lng, lat } = e.lngLat;
            setClickedLocation({ lat, lon: lng, address: null, landmarks: null });
            setIsLoadingAddress(true);
            
            // Fetch reverse geocode and landmarks in parallel
            const [reverseResult, landmarksResult] = await Promise.all([
                fetchReverseGeocode(lat, lng),
                fetchLandmarks(lat, lng)
            ]);
            
            let addressInfo = null;
            if (reverseResult?.status === 'success' && reverseResult.data) {
                addressInfo = reverseResult.data;
            }
            
            let landmarksInfo = null;
            if (landmarksResult?.status === 'success' && landmarksResult.data) {
                landmarksInfo = landmarksResult.data;
            }
            
            setClickedLocation({ 
                lat, 
                lon: lng, 
                address: addressInfo,
                landmarks: landmarksInfo
            });
            setIsLoadingAddress(false);
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

    // Compute zoom-based POI limit
    // Lower zoom (zoomed out) = fewer POIs; higher zoom (zoomed in) = more POIs
    const getLimitForZoom = useCallback((zoom) => {
        if (zoom <= 10) return 100;
        if (zoom <= 12) return 200;
        if (zoom <= 14) return 400;
        if (zoom <= 16) return 800;
        return 1500; // street-level
    }, []);

    // Fetch POIs for current viewport (debounced)
    // Skip viewport fetching if we have filteredPOIs from category search
    const fetchViewportPOIs = useCallback(() => {
        if (!map.current || !mapLoaded || !activeLayers.includes('competitors')) {
            setPois([]);
            return;
        }

        // If we have filtered POIs from search, don't fetch viewport POIs
        if (filteredPOIs && filteredPOIs.length > 0) {
            return;
        }

        // Debounce: clear previous pending fetch
        if (fetchTimeoutRef.current) {
            clearTimeout(fetchTimeoutRef.current);
        }

        fetchTimeoutRef.current = setTimeout(async () => {
            const bounds = map.current.getBounds();
            const zoom = map.current.getZoom();
            const limit = getLimitForZoom(zoom);

            const minLat = bounds.getSouth();
            const maxLat = bounds.getNorth();
            const minLon = bounds.getWest();
            const maxLon = bounds.getEast();

            console.log(`Fetching POIs for viewport: zoom=${zoom.toFixed(1)}, limit=${limit}`);
            const data = await fetchPointsViewport(minLat, minLon, maxLat, maxLon, limit);
            if (data) {
                setPois(data);
                console.log(`Received ${data.length} POIs`);
            }
        }, 150); // 150ms debounce
    }, [mapLoaded, activeLayers, getLimitForZoom, filteredPOIs]);

    // Handle filtered POIs from category/super_category search
    useEffect(() => {
        if (filteredPOIs && filteredPOIs.length > 0) {
            console.log(`Using ${filteredPOIs.length} filtered POIs from search`);
            setPois(filteredPOIs);
            
            // Auto-fit map to show all filtered POIs
            if (map.current && mapLoaded && filteredPOIs.length > 1) {
                const bounds = new maplibregl.LngLatBounds();
                filteredPOIs.forEach(poi => {
                    if (poi.lat && poi.lon) {
                        bounds.extend([poi.lon, poi.lat]);
                    }
                });
                
                // Only fit if bounds are valid
                if (!bounds.isEmpty()) {
                    map.current.fitBounds(bounds, {
                        padding: 50,
                        maxZoom: 14
                    });
                }
            }
        } else if (filteredPOIs === null) {
            // Filter was cleared, refetch viewport POIs
            fetchViewportPOIs();
        }
    }, [filteredPOIs, mapLoaded]);

    // Attach moveend listener to refetch POIs on pan/zoom
    useEffect(() => {
        if (!map.current || !mapLoaded) return;

        const handleMoveEnd = () => {
            fetchViewportPOIs();
        };

        map.current.on('moveend', handleMoveEnd);

        // Initial fetch when layer is active and map ready
        if (activeLayers.includes('competitors')) {
            fetchViewportPOIs();
        }

        return () => {
            if (map.current) {
                map.current.off('moveend', handleMoveEnd);
            }
            if (fetchTimeoutRef.current) {
                clearTimeout(fetchTimeoutRef.current);
            }
        };
    }, [mapLoaded, activeLayers, fetchViewportPOIs]);

    // Clear POIs when competitors layer is disabled
    useEffect(() => {
        if (!activeLayers.includes('competitors')) {
            setPois([]);
        }
    }, [activeLayers]);

    // Add/remove markers
    useEffect(() => {
        if (!map.current || !mapLoaded) return;

        // Clear existing markers
        markersRef.current.forEach(m => m.remove());
        markersRef.current = [];

        // Add POI markers - POIs are already filtered/ranked by backend viewport query
        if (activeLayers.includes('competitors') && pois.length > 0) {
            pois.forEach((poi) => {
                if (!poi.lat || !poi.lon) return;
                
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
            
            console.log(`Rendered ${pois.length} markers for current viewport`);
        }
    }, [pois, activeLayers, mapLoaded]);

    // Handle map center changes from search
    useEffect(() => {
        if (!map.current || !mapLoaded || !mapCenter) return;
        
        map.current.flyTo({
            center: [mapCenter.lon, mapCenter.lat],
            zoom: mapCenter.zoom || 14,
            essential: true
        });
    }, [mapCenter, mapLoaded]);

    // Handle selected location marker from search
    useEffect(() => {
        if (!map.current || !mapLoaded) return;

        // Remove previous selected marker
        if (selectedMarkerRef.current) {
            selectedMarkerRef.current.remove();
            selectedMarkerRef.current = null;
        }

        if (selectedLocation) {
            // Create a distinctive marker for the selected location
            const el = document.createElement('div');
            el.style.width = '24px';
            el.style.height = '24px';
            el.style.backgroundColor = '#EF4444';
            el.style.borderRadius = '50%';
            el.style.border = '3px solid white';
            el.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
            el.style.cursor = 'pointer';

            const marker = new maplibregl.Marker({ element: el })
                .setLngLat([selectedLocation.lon, selectedLocation.lat])
                .setPopup(
                    new maplibregl.Popup({ offset: 25 })
                        .setHTML(`<div style="color:#333;"><b>${selectedLocation.name}</b></div>`)
                )
                .addTo(map.current);

            // Open popup automatically
            marker.togglePopup();
            selectedMarkerRef.current = marker;
        }
    }, [selectedLocation, mapLoaded]);

    // Handle isochrone visualization
    const loadIsochrone = useCallback(async (lat, lon, distance) => {
        if (!map.current || !mapLoaded || !isochroneSourceRef.current) return;

        const result = await fetchIsochrone(lat, lon, distance);
        
        if (result?.status === 'success' && result.data?.geom) {
            const geojsonData = {
                type: 'FeatureCollection',
                features: [{
                    type: 'Feature',
                    geometry: result.data.geom.geometry,
                    properties: { distance }
                }]
            };
            
            map.current.getSource('isochrone').setData(geojsonData);
        }
    }, [mapLoaded]);

    // Clear isochrone
    const clearIsochrone = useCallback(() => {
        if (!map.current || !isochroneSourceRef.current) return;
        
        map.current.getSource('isochrone').setData({
            type: 'FeatureCollection',
            features: []
        });
        setShowIsochrone(false);
    }, []);

    // Load isochrone when clicked location and showIsochrone is enabled
    useEffect(() => {
        if (showIsochrone && clickedLocation) {
            loadIsochrone(clickedLocation.lat, clickedLocation.lon, isochroneDistance);
        }
    }, [showIsochrone, clickedLocation, isochroneDistance, loadIsochrone]);

    return (
        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
            <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
            
            {/* Clicked Location Info Panel */}
            {clickedLocation && (
                <div style={{
                    position: 'absolute',
                    top: '80px',
                    right: '60px',
                    background: 'rgba(255,255,255,0.98)',
                    borderRadius: '12px',
                    padding: '16px',
                    fontSize: '12px',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                    zIndex: 1000,
                    maxWidth: '320px',
                    minWidth: '280px'
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <h4 style={{ fontWeight: 'bold', color: '#333', margin: 0 }}>📍 Location Info</h4>
                        <button 
                            onClick={() => setClickedLocation(null)}
                            style={{ 
                                background: 'none', 
                                border: 'none', 
                                cursor: 'pointer', 
                                fontSize: '16px',
                                color: '#666'
                            }}
                        >
                            ✕
                        </button>
                    </div>
                    
                    {/* Coordinates */}
                    <div style={{ marginBottom: '12px', padding: '8px', background: '#f5f5f5', borderRadius: '6px' }}>
                        <div style={{ color: '#666', fontSize: '10px', marginBottom: '4px' }}>COORDINATES</div>
                        <div style={{ color: '#333', fontFamily: 'monospace' }}>
                            {clickedLocation.lat.toFixed(6)}, {clickedLocation.lon.toFixed(6)}
                        </div>
                    </div>

                    {/* Address */}
                    {isLoadingAddress ? (
                        <div style={{ color: '#666', fontStyle: 'italic' }}>Loading address...</div>
                    ) : clickedLocation.address ? (
                        <div style={{ marginBottom: '12px' }}>
                            <div style={{ color: '#666', fontSize: '10px', marginBottom: '4px' }}>ADDRESS</div>
                            <div style={{ color: '#333', lineHeight: '1.4' }}>
                                {clickedLocation.address.address}
                            </div>
                            {clickedLocation.address.pincode && (
                                <div style={{ color: '#666', marginTop: '4px' }}>
                                    📮 Pincode: {clickedLocation.address.pincode}
                                </div>
                            )}
                            {clickedLocation.address.building_name && (
                                <div style={{ color: '#666', marginTop: '2px' }}>
                                    🏢 {clickedLocation.address.building_name}
                                </div>
                            )}
                        </div>
                    ) : null}

                    {/* Nearby Landmarks */}
                    {clickedLocation.landmarks && clickedLocation.landmarks.length > 0 && (
                        <div style={{ marginBottom: '12px' }}>
                            <div style={{ color: '#666', fontSize: '10px', marginBottom: '4px' }}>NEARBY LANDMARKS</div>
                            <div style={{ maxHeight: '100px', overflowY: 'auto' }}>
                                {clickedLocation.landmarks.slice(0, 4).map((lm, idx) => (
                                    <div key={idx} style={{ color: '#555', padding: '2px 0', borderBottom: '1px solid #eee' }}>
                                        🏛️ {lm.name}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Isochrone Controls */}
                    <div style={{ borderTop: '1px solid #eee', paddingTop: '12px', marginTop: '8px' }}>
                        <div style={{ color: '#666', fontSize: '10px', marginBottom: '8px' }}>REACHABILITY ANALYSIS</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <select 
                                value={isochroneDistance}
                                onChange={(e) => setIsochroneDistance(parseFloat(e.target.value))}
                                style={{ 
                                    padding: '6px 10px', 
                                    borderRadius: '6px', 
                                    border: '1px solid #ddd',
                                    fontSize: '12px',
                                    flex: 1
                                }}
                            >
                                <option value={0.5}>0.5 km</option>
                                <option value={1}>1 km</option>
                                <option value={2}>2 km</option>
                                <option value={3}>3 km</option>
                                <option value={5}>5 km</option>
                            </select>
                            <button
                                onClick={() => {
                                    if (showIsochrone) {
                                        clearIsochrone();
                                    } else {
                                        setShowIsochrone(true);
                                    }
                                }}
                                style={{
                                    padding: '6px 12px',
                                    borderRadius: '6px',
                                    border: 'none',
                                    background: showIsochrone ? '#EF4444' : '#3B82F6',
                                    color: 'white',
                                    cursor: 'pointer',
                                    fontSize: '12px',
                                    fontWeight: '500'
                                }}
                            >
                                {showIsochrone ? 'Clear' : 'Show Area'}
                            </button>
                        </div>
                        {showIsochrone && (
                            <div style={{ color: '#666', fontSize: '10px' }}>
                                Blue area shows reachable region within {isochroneDistance} km
                            </div>
                        )}
                    </div>
                </div>
            )}
            
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
