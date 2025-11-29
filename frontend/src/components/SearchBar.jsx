import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, X, Loader2, AlertCircle, Building2 } from 'lucide-react';
import { fetchAutocomplete, fetchGeocode, searchAreas, checkPointInDelhi } from '../services/api';

// Delhi bounding box from database: Lon [76.8388, 77.3475], Lat [28.4043, 28.8835]
const DELHI_BOUNDS = {
    minLat: 28.4043,
    maxLat: 28.8835,
    minLon: 76.8388,
    maxLon: 77.3475
};

// Quick bounding box check
const isWithinDelhiBounds = (lat, lon) => {
    return (
        lat >= DELHI_BOUNDS.minLat &&
        lat <= DELHI_BOUNDS.maxLat &&
        lon >= DELHI_BOUNDS.minLon &&
        lon <= DELHI_BOUNDS.maxLon
    );
};

const SearchBar = ({ onLocationSelect }) => {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const [error, setError] = useState(null);
    const inputRef = useRef(null);
    const dropdownRef = useRef(null);
    const debounceRef = useRef(null);

    // Debounced hybrid search: local areas + external API
    useEffect(() => {
        if (debounceRef.current) {
            clearTimeout(debounceRef.current);
        }

        if (query.length < 2) {
            setSuggestions([]);
            setShowDropdown(false);
            setError(null);
            return;
        }

        setIsLoading(true);
        setError(null);
        debounceRef.current = setTimeout(async () => {
            // Search both local database and external API in parallel
            const [localResults, externalResult] = await Promise.all([
                searchAreas(query, 5),  // Local Delhi areas from database
                fetchAutocomplete(query, 28.6139, 77.1025, 5)  // External API
            ]);

            const combinedSuggestions = [];

            // Add local area results first (guaranteed to be in Delhi)
            if (localResults && localResults.length > 0) {
                localResults.forEach(area => {
                    combinedSuggestions.push({
                        name: area.name,
                        lat: area.lat,
                        lon: area.lon,
                        type: 'area',
                        source: 'local'
                    });
                });
            }

            // Add external results (filter for Delhi-related)
            if (externalResult?.status === 'success' && externalResult.data) {
                externalResult.data.forEach(item => {
                    // Avoid duplicates with local results
                    const isDuplicate = combinedSuggestions.some(
                        s => s.name.toLowerCase() === item.name.toLowerCase()
                    );
                    if (!isDuplicate) {
                        combinedSuggestions.push({
                            name: item.name,
                            geoid: item.geoid,
                            type: 'external',
                            source: 'latlong'
                        });
                    }
                });
            }

            setSuggestions(combinedSuggestions);
            setShowDropdown(combinedSuggestions.length > 0);
            setIsLoading(false);
        }, 300);

        return () => {
            if (debounceRef.current) {
                clearTimeout(debounceRef.current);
            }
        };
    }, [query]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (
                dropdownRef.current && 
                !dropdownRef.current.contains(event.target) &&
                inputRef.current &&
                !inputRef.current.contains(event.target)
            ) {
                setShowDropdown(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Handle keyboard navigation
    const handleKeyDown = (e) => {
        if (!showDropdown || suggestions.length === 0) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex(prev => 
                    prev < suggestions.length - 1 ? prev + 1 : prev
                );
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
                    handleSelect(suggestions[selectedIndex]);
                }
                break;
            case 'Escape':
                setShowDropdown(false);
                setSelectedIndex(-1);
                break;
            default:
                break;
        }
    };

    // Handle selection of a suggestion
    const handleSelect = async (suggestion) => {
        setShowDropdown(false);
        setSelectedIndex(-1);
        setIsLoading(true);
        setError(null);

        let lat, lon;

        // If it's a local area result, we already have coordinates
        if (suggestion.source === 'local' && suggestion.lat && suggestion.lon) {
            lat = suggestion.lat;
            lon = suggestion.lon;
        } else {
            // External result - need to geocode
            const geocodeResult = await fetchGeocode(suggestion.name);
            
            if (geocodeResult?.status === 'success' && geocodeResult.data) {
                lat = parseFloat(geocodeResult.data.latitude);
                lon = parseFloat(geocodeResult.data.longitude);
            } else {
                setError('Could not find coordinates for this location.');
                setIsLoading(false);
                return;
            }
        }

        // Quick bounding box check first
        if (!isWithinDelhiBounds(lat, lon)) {
            setError('This location is outside Delhi. Please select a location within Delhi NCT.');
            setQuery('');
            setIsLoading(false);
            return;
        }

        // For external results, do precise geometry check against database
        if (suggestion.source !== 'local') {
            const isInDelhi = await checkPointInDelhi(lat, lon);
            if (!isInDelhi) {
                setError('This location is outside Delhi city boundaries. Please select a location within Delhi NCT.');
                setQuery('');
                setIsLoading(false);
                return;
            }
        }

        setQuery(suggestion.name);
        onLocationSelect({
            name: suggestion.name,
            lat: lat,
            lon: lon,
            type: suggestion.type,
            geoid: suggestion.geoid
        });
        
        setIsLoading(false);
    };

    // Clear search
    const handleClear = () => {
        setQuery('');
        setSuggestions([]);
        setShowDropdown(false);
        setSelectedIndex(-1);
        setError(null);
        inputRef.current?.focus();
    };

    return (
        <div className="relative w-full max-w-md">
            {/* Error Message */}
            {error && (
                <div className="absolute bottom-full left-0 right-0 mb-2 bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2 shadow-lg z-[1002]">
                    <AlertCircle size={16} className="text-red-500 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <p className="text-sm text-red-700">{error}</p>
                    </div>
                    <button 
                        onClick={() => setError(null)}
                        className="text-red-400 hover:text-red-600"
                    >
                        <X size={14} />
                    </button>
                </div>
            )}
            
            {/* Search Input */}
            <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    {isLoading ? (
                        <Loader2 size={18} className="text-gray-400 animate-spin" />
                    ) : (
                        <Search size={18} className="text-gray-400" />
                    )}
                </div>
                <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => { setQuery(e.target.value); setError(null); }}
                    onKeyDown={handleKeyDown}
                    onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
                    placeholder="Search locations in Delhi..."
                    className={`w-full pl-10 pr-10 py-2.5 bg-white/95 backdrop-blur-sm border rounded-xl text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:border-transparent shadow-lg ${
                        error ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-blue-500'
                    }`}
                />
                {query && (
                    <button
                        onClick={handleClear}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center hover:text-gray-700"
                    >
                        <X size={18} className="text-gray-400" />
                    </button>
                )}
            </div>

            {/* Autocomplete Dropdown */}
            {showDropdown && suggestions.length > 0 && (
                <div
                    ref={dropdownRef}
                    className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-[1001] max-h-80 overflow-y-auto"
                >
                    {suggestions.map((suggestion, index) => {
                        const isLocal = suggestion.source === 'local';
                        return (
                            <button
                                key={suggestion.geoid || `${suggestion.name}-${index}`}
                                onClick={() => handleSelect(suggestion)}
                                onMouseEnter={() => setSelectedIndex(index)}
                                className={`w-full px-4 py-3 flex items-start gap-3 text-left transition-colors ${
                                    index === selectedIndex 
                                        ? 'bg-blue-50' 
                                        : 'hover:bg-gray-50'
                                }`}
                            >
                                {isLocal ? (
                                    <Building2 size={16} className="mt-0.5 flex-shrink-0 text-green-600" />
                                ) : (
                                    <MapPin size={16} className="mt-0.5 flex-shrink-0 text-blue-500" />
                                )}
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-gray-800 truncate">
                                        {suggestion.name}
                                    </p>
                                    <p className={`text-xs mt-0.5 ${isLocal ? 'text-green-600' : 'text-gray-400'}`}>
                                        {isLocal ? '✓ Delhi Area' : 'External location'}
                                    </p>
                                </div>
                            </button>
                        );
                    })}
                </div>
            )}

            {/* No results message */}
            {showDropdown && query.length >= 2 && suggestions.length === 0 && !isLoading && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-gray-200 p-4 z-[1001]">
                    <p className="text-sm text-gray-500 text-center">No locations found</p>
                </div>
            )}
        </div>
    );
};

export default SearchBar;
