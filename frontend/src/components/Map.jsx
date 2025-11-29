import React, { useEffect, useState } from 'react';
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

    const handleLocationSelect = async (latlng) => {
        setSelectedLocation(latlng);
        // Fetch isochrone
        const iso = await fetchIsochrone(latlng.lat, latlng.lng, 15);
        if (iso) setIsochrone(iso);
        
        // Example: Fetch external POIs near the click
        // const extPois = await fetchExternalPOI(latlng.lat, latlng.lng);
        // console.log("External POIs:", extPois);
    };

    return (
        <MapContainer center={DELHI_CENTER} zoom={11} style={{ height: '100%', width: '100%' }}>
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            
            {boundary && <GeoJSON key="boundary" data={boundary} style={{ color: 'blue', fillOpacity: 0.1 }} />}
            
            {pois.map(poi => (
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
