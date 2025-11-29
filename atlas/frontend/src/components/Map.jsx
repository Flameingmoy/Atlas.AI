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

// Color mapping for POI categories
const getCategoryColor = (category) => {
    const colorMap = {
        'Restaurant': '#EF4444',    // Red
        'Cafe': '#F59E0B',          // Amber/Orange
        'Mall': '#8B5CF6',          // Purple
        'Monument': '#10B981',      // Green
        'Market': '#EC4899',        // Pink
        'Hospital': '#3B82F6',      // Blue
        'Metro Station': '#F97316', // Orange
        'default': '#6B7280'        // Gray
    };
    return colorMap[category] || colorMap['default'];
};

const Map = ({ activeLayers }) => {
    const [pois, setPois] = useState([]);
    const [lng, setLng] = useState(77.2090);
    const [lat, setLat] = useState(28.6139);
    const [heatmapPoints, setHeatmapPoints] = useState([]);

    // Delhi Center
    const position = [28.6139, 77.2090];

    useEffect(() => {
        const loadData = async () => {
            const data = await fetchPOIs();
            setPois(data);

            // Mock Heatmap Data (Delhi)
            setHeatmapPoints([
                { lat: 28.6139, lon: 77.2090, intensity: 1.0 }, // Connaught Place
                { lat: 28.5244, lon: 77.1855, intensity: 0.9 }, // Hauz Khas
                { lat: 28.6692, lon: 77.4538, intensity: 0.8 }, // Noida
                { lat: 28.5355, lon: 77.3910, intensity: 0.7 }, // Nehru Place
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
            {activeLayers.includes('competitors') && pois.map((poi, idx) => {
                const categoryColor = getCategoryColor(poi.category);
                return (
                    <CircleMarker
                        key={`poi-${idx}`}
                        center={[poi.lat, poi.lon]}
                        pathOptions={{ 
                            color: categoryColor, 
                            fillColor: categoryColor, 
                            fillOpacity: 0.7,
                            weight: 2
                        }}
                        radius={6}
                    >
                        <Popup>
                            <div className="text-gray-900">
                                <h3 className="font-bold">{poi.name}</h3>
                                <p className="text-sm">Category: {poi.category || 'Unknown'}</p>
                                <div 
                                    className="inline-block w-3 h-3 rounded-full mt-1" 
                                    style={{ backgroundColor: categoryColor }}
                                ></div>
                            </div>
                        </Popup>
                    </CircleMarker>
                );
            })}

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

            {/* Category Legend */}
            {activeLayers.includes('competitors') && (
                <div className="leaflet-bottom leaflet-right">
                    <div className="leaflet-control" style={{ marginBottom: '10px', marginRight: '10px' }}>
                        <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-xl p-3 text-xs">
                            <h4 className="font-bold text-gray-800 mb-2">Categories</h4>
                            <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#EF4444' }}></div>
                                    <span className="text-gray-700">Restaurant</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#F59E0B' }}></div>
                                    <span className="text-gray-700">Cafe</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#8B5CF6' }}></div>
                                    <span className="text-gray-700">Mall</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#10B981' }}></div>
                                    <span className="text-gray-700">Monument</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#EC4899' }}></div>
                                    <span className="text-gray-700">Market</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3B82F6' }}></div>
                                    <span className="text-gray-700">Hospital</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#F97316' }}></div>
                                    <span className="text-gray-700">Metro Station</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

        </MapContainer>
    );
};

export default Map;
