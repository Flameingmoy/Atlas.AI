import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, X, Loader2, AlertCircle, Building2, Tag, Layers } from 'lucide-react';
import { unifiedSearch, fetchPOIsByCategory, fetchPOIsBySuperCategory, fetchAutocomplete, fetchGeocode, checkPointInDelhi } from '../services/api';

// Delhi bounding box from database
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

// Icon mapping for different result types
const getIcon = (type) => {
    switch (type) {
        case 'area':
            return <Building2 size={16} className="text-green-600" />;
        case 'category':
            return <Tag size={16} className="text-green-600" />;
        case 'super_category':
            return <Layers size={16} className="text-green-600" />;
        case 'poi':
            return <MapPin size={16} className="text-green-600" />;
        case 'external':
            return <MapPin size={16} className="text-gray-400" />;
        default:
            return <MapPin size={16} className="text-gray-400" />;
    }
};

// Label and color mapping for result types
const getTypeInfo = (type, count, category) => {
    switch (type) {
        case 'area':
            return {
                label: '✓ Delhi Area',
                className: 'text-green-600'
            };
        case 'category':
            return {
                label: `✓ Category · ${count?.toLocaleString()} places`,
                className: 'text-green-600'
            };
        case 'super_category':
            return {
                label: `✓ Super Category · ${count?.toLocaleString()} places`,
                className: 'text-green-600'
            };
        case 'poi':
            return {
                label: `✓ ${category || 'Delhi POI'}`,
                className: 'text-green-600'
            };
        case 'external':
            return {
                label: 'External location',
                className: 'text-gray-400'
            };
        default:
            return {
                label: '',
                className: 'text-gray-400'
            };
    }
};

const SearchBar = ({ onLocationSelect, onCategorySelect, onPOIsLoad }) => {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const [error, setError] = useState(null);
    const [activeFilter, setActiveFilter] = useState(null);
    const inputRef = useRef(null);
    const dropdownRef = useRef(null);
    const debounceRef = useRef(null);

    // Debounced unified search + external API
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

        // Don't search if query starts with "Category:" or "Super Category:"
        if (query.startsWith('Category:') || query.startsWith('Super Category:')) {
            return;
        }

        setIsLoading(true);
        setError(null);
        debounceRef.current = setTimeout(async () => {
            // Search both local database and external API in parallel
            const [localResults, externalResult] = await Promise.all([
                unifiedSearch(query, 12),
                fetchAutocomplete(query, 28.6139, 77.1025, 5)
            ]);

            const combinedSuggestions = [...localResults];

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

        const { type } = suggestion;

        try {
            if (type === 'area') {
                // Area selection - navigate to location
                const { lat, lon, name } = suggestion;
                
                if (!isWithinDelhiBounds(lat, lon)) {
                    setError('This location is outside Delhi bounds.');
                    setIsLoading(false);
                    return;
                }

                setQuery(name);
                setActiveFilter(null);
                onLocationSelect?.({
                    name,
                    lat,
                    lon,
                    type: 'area'
                });
            } else if (type === 'poi') {
                // POI selection - navigate to specific POI
                const { lat, lon, name, category } = suggestion;
                
                if (!isWithinDelhiBounds(lat, lon)) {
                    setError('This POI is outside Delhi bounds.');
                    setIsLoading(false);
                    return;
                }

                setQuery(name);
                setActiveFilter(null);
                onLocationSelect?.({
                    name,
                    lat,
                    lon,
                    type: 'poi',
                    category
                });
            } else if (type === 'category') {
                // Category selection - load all POIs of this category
                const { name, count } = suggestion;
                setQuery(`Category: ${name}`);
                setActiveFilter({ type: 'category', name, count });
                
                const pois = await fetchPOIsByCategory(name, 2000);
                onPOIsLoad?.({
                    pois,
                    filterType: 'category',
                    filterName: name,
                    count
                });
                onCategorySelect?.({ type: 'category', name, count });
            } else if (type === 'super_category') {
                // Super category selection - load all POIs of this super category
                const { name, count } = suggestion;
                setQuery(`Super Category: ${name}`);
                setActiveFilter({ type: 'super_category', name, count });
                
                const pois = await fetchPOIsBySuperCategory(name, 2000);
                onPOIsLoad?.({
                    pois,
                    filterType: 'super_category',
                    filterName: name,
                    count
                });
                onCategorySelect?.({ type: 'super_category', name, count });
            } else if (type === 'external') {
                // External result - need to geocode first
                const geocodeResult = await fetchGeocode(suggestion.name);
                
                if (geocodeResult?.status === 'success' && geocodeResult.data) {
                    const lat = parseFloat(geocodeResult.data.latitude);
                    const lon = parseFloat(geocodeResult.data.longitude);
                    
                    // Quick bounding box check first
                    if (!isWithinDelhiBounds(lat, lon)) {
                        setError('This location is outside Delhi. Please select a location within Delhi NCT.');
                        setQuery('');
                        setIsLoading(false);
                        return;
                    }
                    
                    // Do precise geometry check against database
                    const isInDelhi = await checkPointInDelhi(lat, lon);
                    if (!isInDelhi) {
                        setError('This location is outside Delhi city boundaries. Please select a location within Delhi NCT.');
                        setQuery('');
                        setIsLoading(false);
                        return;
                    }
                    
                    setQuery(suggestion.name);
                    setActiveFilter(null);
                    onLocationSelect?.({
                        name: suggestion.name,
                        lat,
                        lon,
                        type: 'external',
                        geoid: suggestion.geoid
                    });
                } else {
                    setError('Could not find coordinates for this location.');
                }
            }
        } catch (err) {
            console.error('Selection error:', err);
            setError('Failed to process selection. Please try again.');
        }
        
        setIsLoading(false);
    };

    // Clear search and filter
    const handleClear = () => {
        setQuery('');
        setSuggestions([]);
        setShowDropdown(false);
        setSelectedIndex(-1);
        setError(null);
        setActiveFilter(null);
        onCategorySelect?.(null);
        inputRef.current?.focus();
    };

    return (
        <div className="relative w-full max-w-md">
            {/* Active Filter Badge */}
            {activeFilter && (
                <div className="absolute bottom-full left-0 right-0 mb-2 flex items-center gap-2">
                    <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                        activeFilter.type === 'category' 
                            ? 'bg-purple-100 text-purple-700' 
                            : 'bg-orange-100 text-orange-700'
                    }`}>
                        {activeFilter.type === 'category' ? <Tag size={12} /> : <Layers size={12} />}
                        <span>{activeFilter.name}</span>
                        <span className="opacity-70">({activeFilter.count?.toLocaleString()})</span>
                    </div>
                </div>
            )}

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
                    onChange={(e) => { setQuery(e.target.value); setError(null); setActiveFilter(null); }}
                    onKeyDown={handleKeyDown}
                    onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
                    placeholder="Search areas, POIs, categories..."
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
                    className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-[1001] max-h-96 overflow-y-auto"
                >
                    {suggestions.map((suggestion, index) => {
                        const typeInfo = getTypeInfo(suggestion.type, suggestion.count, suggestion.category);
                        return (
                            <button
                                key={`${suggestion.type}-${suggestion.name}-${index}`}
                                onClick={() => handleSelect(suggestion)}
                                onMouseEnter={() => setSelectedIndex(index)}
                                className={`w-full px-4 py-3 flex items-start gap-3 text-left transition-colors ${
                                    index === selectedIndex 
                                        ? 'bg-blue-50' 
                                        : 'hover:bg-gray-50'
                                }`}
                            >
                                <div className="mt-0.5 flex-shrink-0">
                                    {getIcon(suggestion.type)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-gray-800 truncate">
                                        {suggestion.name}
                                    </p>
                                    <p className={`text-xs mt-0.5 ${typeInfo.className}`}>
                                        {typeInfo.label}
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
                    <p className="text-sm text-gray-500 text-center">No results found for "{query}"</p>
                    <p className="text-xs text-gray-400 text-center mt-1">Try searching for areas, categories, or POI names</p>
                </div>
            )}
        </div>
    );
};

export default SearchBar;
