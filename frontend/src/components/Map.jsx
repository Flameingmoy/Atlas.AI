import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { fetchPOIs, fetchBoundary, fetchExternalPOI, fetchIsochrone } from '../services/api';

// Fix Leaflet marker icon issue
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const DELHI_CENTER = [28.6139, 77.1025]; // Lat, Lng
const RADIUS_KM = 30; // 30km radius
const PADDING_KM = 10; // 10km padding

// Helper to create circle polygon coordinates [lng, lat] for GeoJSON
// Adjusts for latitude distortion to create a visual circle
const createCirclePolygon = (centerLat, centerLng, radiusKm, steps = 64) => {
    const coordinates = [];
    const latRad = centerLat * (Math.PI / 180);
    const kmPerDegLat = 111.32;
    const kmPerDegLng = 111.32 * Math.cos(latRad);

    const radiusDegLat = radiusKm / kmPerDegLat;
    const radiusDegLng = radiusKm / kmPerDegLng;

    for (let i = 0; i < steps; i++) {
        const angle = (i / steps) * 2 * Math.PI;
        const dLat = radiusDegLat * Math.cos(angle);
        const dLng = radiusDegLng * Math.sin(angle); 
        coordinates.push([centerLng + dLng, centerLat + dLat]);
    }
    coordinates.push(coordinates[0]); // Close ring
    return coordinates;
};

function LocationMarker({ onLocationSelect }) {
    const [position, setPosition] = useState(null);
    const map = useMapEvents({
        click(e) {
            setPosition(e.latlng);
            onLocationSelect(e.latlng);
        },
    });

    return position === null ? null : (
        <Marker position={position}>
            <Popup>Selected Location</Popup>
        </Marker>
    );
}

const Map = ({ activeLayers }) => {
    const [pois, setPois] = useState([]);
    const [boundary, setBoundary] = useState(null);
    const [isochrone, setIsochrone] = useState(null);
    const [selectedLocation, setSelectedLocation] = useState(null);

    // Generate the mask GeoJSON (World minus Delhi Circle)
    const maskGeoJSON = useMemo(() => {
        const circleRing = createCirclePolygon(DELHI_CENTER[0], DELHI_CENTER[1], RADIUS_KM);
        return {
            type: "Feature",
            geometry: {
                type: "Polygon",
                coordinates: [
                    // Outer ring (World) - Counter-Clockwise
                    [[-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]],
                    // Inner ring (Hole - Delhi Circle) - Clockwise
                    circleRing
                ]
            }
        };
    }, []);

    // Calculate Max Bounds based on KM
    const maxBounds = useMemo(() => {
        const latRad = DELHI_CENTER[0] * (Math.PI / 180);
        const kmPerDegLat = 111.32;
        const kmPerDegLng = 111.32 * Math.cos(latRad);
        
        const totalRadiusKm = RADIUS_KM + PADDING_KM;
        const latOffset = totalRadiusKm / kmPerDegLat;
        const lngOffset = totalRadiusKm / kmPerDegLng;

        return [
            [DELHI_CENTER[0] - latOffset, DELHI_CENTER[1] - lngOffset],
            [DELHI_CENTER[0] + latOffset, DELHI_CENTER[1] + lngOffset]
        ];
    }, []);

    useEffect(() => {
        // Load boundary
        fetchBoundary().then(data => {
            if (data) setBoundary(data);
        });
    }, []);

    useEffect(() => {
        // Load POIs if layer active
        if (activeLayers.includes('competitors')) {
            fetchPOIs().then(data => {
                if (data) setPois(data);
            });
        } else {
            setPois([]);
        }
    }, [activeLayers]);

    // Filter POIs to only those within the circle
    const visiblePois = useMemo(() => {
        const latRad = DELHI_CENTER[0] * (Math.PI / 180);
        const kmPerDegLat = 111.32;
        const kmPerDegLng = 111.32 * Math.cos(latRad);
        const radiusDegLat = RADIUS_KM / kmPerDegLat;

        return pois.filter(p => {
            const dLat = p.lat - DELHI_CENTER[0];
            const dLng = (p.lon - DELHI_CENTER[1]) * Math.cos(latRad); // Adjust lng for distance calc
            // Approximate Euclidean distance in degrees (normalized to lat degrees)
            return Math.sqrt(dLat*dLat + dLng*dLng) <= radiusDegLat;
        });
    }, [pois]);

    const handleLocationSelect = async (latlng) => {
        setSelectedLocation(latlng);
        // Fetch isochrone
        const iso = await fetchIsochrone(latlng.lat, latlng.lng, 15);
        if (iso) setIsochrone(iso);
    };

    return (
        <MapContainer 
            center={DELHI_CENTER} 
            zoom={11} 
            minZoom={10}
            maxBounds={maxBounds}
            maxBoundsViscosity={1.0}
            style={{ height: '100%', width: '100%', background: '#1a1a1a' }}
        >
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            
            {/* Mask Layer - Dulls out everything outside Delhi */}
            <GeoJSON 
                data={maskGeoJSON} 
                style={{ 
                    color: 'transparent', 
                    fillColor: '#000000', 
                    fillOpacity: 0.7,
                    weight: 0
                }} 
                interactive={false}
            />

            {/* Official Boundary (Optional, for reference) */}
            {boundary && <GeoJSON key="boundary" data={boundary} style={{ color: '#3b82f6', fillOpacity: 0, weight: 2 }} interactive={false} />}
            
            {/* POIs - Filtered */}
            {visiblePois.map(poi => (
                <Marker key={poi.id} position={[poi.lat, poi.lon]}>
                    <Popup>
                        <b>{poi.name}</b><br/>
                        {poi.category}
                    </Popup>
                </Marker>
            ))}

            {isochrone && <GeoJSON key={`iso-${selectedLocation?.lat}-${selectedLocation?.lng}`} data={isochrone} style={{ color: 'green', fillOpacity: 0.3 }} />}

            <LocationMarker onLocationSelect={handleLocationSelect} />
        </MapContainer>
    );
};

export default Map;
