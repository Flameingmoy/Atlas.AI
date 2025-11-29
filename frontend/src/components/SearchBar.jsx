import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, X, Loader2, AlertCircle } from 'lucide-react';
import { fetchAutocomplete, fetchGeocode } from '../services/api';

// Delhi bounding box (approximate) - used for quick validation
const DELHI_BOUNDS = {
    minLat: 28.40,
    maxLat: 28.90,
    minLon: 76.80,
    maxLon: 77.35
};

// Check if coordinates are within Delhi bounds
const isWithinDelhi = (lat, lon) => {
    return (
        lat >= DELHI_BOUNDS.minLat &&
        lat <= DELHI_BOUNDS.maxLat &&
        lon >= DELHI_BOUNDS.minLon &&
        lon <= DELHI_BOUNDS.maxLon
    );
};

// Check if suggestion name likely refers to Delhi
const isLikelyDelhi = (name) => {
    const lowerName = name.toLowerCase();
    return (
        lowerName.includes('delhi') ||
        lowerName.includes('new delhi') ||
        lowerName.includes('ncr') ||
        lowerName.includes('noida') ||
        lowerName.includes('gurgaon') ||
        lowerName.includes('gurugram') ||
        lowerName.includes('faridabad') ||
        lowerName.includes('ghaziabad')
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

    // Debounced autocomplete search
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
            // Bias results towards Delhi
            const result = await fetchAutocomplete(query, 28.6139, 77.1025, 10);
            
            if (result.status === 'success' && result.data) {
                // Filter suggestions to prioritize Delhi-related results
                const filteredSuggestions = result.data.filter(s => isLikelyDelhi(s.name));
                
                // If we have Delhi results, show them; otherwise show all with a note
                if (filteredSuggestions.length > 0) {
                    setSuggestions(filteredSuggestions);
                } else {
                    // Show original results but they'll be validated on selection
                    setSuggestions(result.data);
                }
                setShowDropdown(true);
            } else {
                setSuggestions([]);
            }
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

        // Geocode the selected address to get coordinates
        const geocodeResult = await fetchGeocode(suggestion.name);
        
        if (geocodeResult?.status === 'success' && geocodeResult.data) {
            const lat = parseFloat(geocodeResult.data.latitude);
            const lon = parseFloat(geocodeResult.data.longitude);
            
            // Validate that the location is within Delhi bounds
            if (!isWithinDelhi(lat, lon)) {
                setError('This location is outside Delhi. Please select a location within Delhi NCT.');
                setQuery('');
                setIsLoading(false);
                return;
            }
            
            setQuery(suggestion.name);
            onLocationSelect({
                name: suggestion.name,
                lat: lat,
                lon: lon,
                geoid: suggestion.geoid
            });
        } else {
            setError('Could not find coordinates for this location.');
        }
        
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
                        const inDelhi = isLikelyDelhi(suggestion.name);
                        return (
                            <button
                                key={suggestion.geoid || index}
                                onClick={() => handleSelect(suggestion)}
                                onMouseEnter={() => setSelectedIndex(index)}
                                className={`w-full px-4 py-3 flex items-start gap-3 text-left transition-colors ${
                                    index === selectedIndex 
                                        ? 'bg-blue-50' 
                                        : 'hover:bg-gray-50'
                                } ${!inDelhi ? 'opacity-60' : ''}`}
                            >
                                <MapPin size={16} className={`mt-0.5 flex-shrink-0 ${inDelhi ? 'text-blue-500' : 'text-gray-400'}`} />
                                <div className="flex-1 min-w-0">
                                    <p className={`text-sm truncate ${inDelhi ? 'text-gray-800' : 'text-gray-500'}`}>
                                        {suggestion.name}
                                    </p>
                                    {!inDelhi && (
                                        <p className="text-xs text-orange-500 mt-0.5">
                                            May be outside Delhi
                                        </p>
                                    )}
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
