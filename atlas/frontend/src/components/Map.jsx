import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchPOIs } from '../services/api';

// Fix for default Leaflet icon issues in React
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// Component to handle map updates
const MapUpdater = ({ center, zoom }) => {
    const map = useMap();
    map.setView(center, zoom);
    return null;
};

const Map = ({ activeLayers }) => {
    const [pois, setPois] = useState([]);
    const [lng, setLng] = useState(77.5946);
    const [lat, setLat] = useState(12.9716);
    const [heatmapPoints, setHeatmapPoints] = useState([]);

    // Bangalore Center
    const position = [12.9716, 77.5946];

    useEffect(() => {
        const loadData = async () => {
            const data = await fetchPOIs();
            setPois(data);

            // Mock Heatmap Data (Bangalore)
            setHeatmapPoints([
                { lat: 12.9716, lon: 77.5946, intensity: 1.0 }, // MG Road area
                { lat: 12.9352, lon: 77.6245, intensity: 0.9 }, // Koramangala
                { lat: 12.9784, lon: 77.6408, intensity: 0.8 }, // Indiranagar
                { lat: 13.0012, lon: 77.5703, intensity: 0.7 }, // Malleshwaram
            ]);
        };
        loadData();
    }, []);

    return (
        <MapContainer
            center={position}
            zoom={13}
            style={{ height: '100%', width: '100%', background: '#111' }}
            zoomControl={false}
        >
            {/* Dark Matter Tiles (Free, No Key) */}
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />

            {/* Competitors Layer */}
            {activeLayers.includes('competitors') && pois.map((poi, idx) => (
                <CircleMarker
                    key={`poi-${idx}`}
                    center={[poi.lat, poi.lon]}
                    pathOptions={{ color: '#F87171', fillColor: '#F87171', fillOpacity: 0.7 }}
                    radius={6}
                >
                    <Popup>
                        <div className="text-gray-900">
                            <h3 className="font-bold">{poi.name}</h3>
                            <p className="text-sm">Category: {poi.category || 'Retail'}</p>
                        </div>
                    </Popup>
                </CircleMarker>
            ))}

            {/* Simple Heatmap Simulation (Circles for now, real heatmap needs plugin) */}
            {activeLayers.includes('heatmap') && heatmapPoints.map((pt, idx) => (
                <CircleMarker
                    key={`heat-${idx}`}
                    center={[pt.lat, pt.lon]}
                    pathOptions={{
                        color: 'transparent',
                        fillColor: pt.intensity > 0.8 ? '#ef4444' : pt.intensity > 0.5 ? '#eab308' : '#3b82f6',
                        fillOpacity: 0.4
                    }}
                    radius={30}
                />
            ))}

        </MapContainer>
    );
};

export default Map;
