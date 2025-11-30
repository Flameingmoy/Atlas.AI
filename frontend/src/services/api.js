import axios from 'axios';

// In development, the Vite proxy should forward /api to the backend
// In production, nginx routes /api to the backend
const API_URL = '/api/v1';

// ============================================
// Caching Layer
// ============================================

// Simple LRU-like cache with TTL
class APICache {
    constructor(maxSize = 500, defaultTTL = 5 * 60 * 1000) { // 5 min default TTL
        this.cache = new Map();
        this.maxSize = maxSize;
        this.defaultTTL = defaultTTL;
    }

    // Generate cache key from URL and params
    makeKey(url, params = {}) {
        const sortedParams = Object.keys(params).sort().map(k => `${k}=${params[k]}`).join('&');
        return `${url}?${sortedParams}`;
    }

    get(key) {
        const entry = this.cache.get(key);
        if (!entry) return null;
        
        // Check TTL
        if (Date.now() > entry.expiry) {
            this.cache.delete(key);
            return null;
        }
        
        // Move to end (most recently used)
        this.cache.delete(key);
        this.cache.set(key, entry);
        return entry.data;
    }

    set(key, data, ttl = this.defaultTTL) {
        // Evict oldest if at capacity
        if (this.cache.size >= this.maxSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
        
        this.cache.set(key, {
            data,
            expiry: Date.now() + ttl
        });
    }

    // For viewport queries, use spatial bucketing
    makeViewportKey(minLat, minLon, maxLat, maxLon, limit) {
        // Round to 3 decimal places (~100m precision) to increase cache hits
        const round = (n) => Math.round(n * 1000) / 1000;
        return `viewport:${round(minLat)},${round(minLon)},${round(maxLat)},${round(maxLon)}:${limit}`;
    }

    clear() {
        this.cache.clear();
    }

    get size() {
        return this.cache.size;
    }
}

// Global cache instances
const cache = new APICache(500, 5 * 60 * 1000);      // 5 min for general queries
const viewportCache = new APICache(100, 30 * 1000); // 30 sec for viewport (changes often)
const staticCache = new APICache(50, 60 * 60 * 1000); // 1 hour for static data (categories, areas)

// ============================================
// Cached API wrapper
// ============================================

const cachedGet = async (url, params = {}, cacheInstance = cache, ttl = null) => {
    const key = cacheInstance.makeKey(url, params);
    
    // Check cache first
    const cached = cacheInstance.get(key);
    if (cached !== null) {
        console.log(`[Cache HIT] ${key}`);
        return cached;
    }
    
    console.log(`[Cache MISS] ${key}`);
    const response = await axios.get(url, { params });
    const data = response.data;
    
    // Store in cache
    if (ttl) {
        cacheInstance.set(key, data, ttl);
    } else {
        cacheInstance.set(key, data);
    }
    
    return data;
};

// ============================================
// API Functions (with caching)
// ============================================

export const fetchPoints = async (category) => {
    try {
        return await cachedGet(`${API_URL}/points`, { category });
    } catch (error) {
        console.error("Error fetching points:", error);
        return [];
    }
};

// Backward compatibility alias
export const fetchPOIs = fetchPoints;

/**
 * Fetch POIs within a viewport bounding box, ranked by importance.
 * Uses spatial bucketing for cache efficiency.
 */
export const fetchPointsViewport = async (minLat, minLon, maxLat, maxLon, limit = 200, bufferFrac = 0.05) => {
    try {
        const key = viewportCache.makeViewportKey(minLat, minLon, maxLat, maxLon, limit);
        
        // Check viewport cache
        const cached = viewportCache.get(key);
        if (cached !== null) {
            console.log(`[Viewport Cache HIT] ${limit} POIs`);
            return cached;
        }
        
        console.log(`[Viewport Cache MISS] Fetching ${limit} POIs`);
        const response = await axios.get(`${API_URL}/points/viewport`, {
            params: { min_lat: minLat, min_lon: minLon, max_lat: maxLat, max_lon: maxLon, limit, buffer_frac: bufferFrac }
        });
        
        viewportCache.set(key, response.data);
        return response.data;
    } catch (error) {
        console.error("Error fetching viewport points:", error);
        return [];
    }
};

export const fetchClusters = async (points) => {
    try {
        const response = await axios.post(`${API_URL}/analyze/clusters`, points);
        return response.data;
    } catch (error) {
        console.error("Error fetching clusters:", error);
        return null;
    }
}

export const sendChatMessage = async (message) => {
    try {
        const response = await axios.post(`${API_URL}/chat`, { message });
        return response.data;
    } catch (error) {
        console.error("Error sending chat message:", error);
        return { text: "Sorry, I encountered an error.", actions: [] };
    }
}

export const fetchBoundary = async () => {
    try {
        return await cachedGet(`${API_URL}/delhi_boundary`, {}, staticCache);
    } catch (error) {
        console.error("Error fetching boundary:", error);
        return null;
    }
};

// ============================================
// Delhi Database API Functions
// ============================================

/**
 * Search areas within Delhi by name
 */
export const searchAreas = async (query, limit = 10) => {
    try {
        return await cachedGet(`${API_URL}/areas/search`, { q: query, limit });
    } catch (error) {
        console.error("Error searching areas:", error);
        return [];
    }
};

/**
 * Unified search across areas, POIs, categories, and super categories
 */
export const unifiedSearch = async (query, limit = 15) => {
    try {
        return await cachedGet(`${API_URL}/search/unified`, { q: query, limit });
    } catch (error) {
        console.error("Error in unified search:", error);
        return [];
    }
};

/**
 * Search POIs by name
 */
export const searchPOIs = async (query, limit = 10) => {
    try {
        return await cachedGet(`${API_URL}/pois/search`, { q: query, limit });
    } catch (error) {
        console.error("Error searching POIs:", error);
        return [];
    }
};

/**
 * Search categories
 */
export const searchCategories = async (query, limit = 10) => {
    try {
        return await cachedGet(`${API_URL}/categories/search`, { q: query, limit });
    } catch (error) {
        console.error("Error searching categories:", error);
        return [];
    }
};

/**
 * Get all categories (static, long cache)
 */
export const fetchCategories = async () => {
    try {
        return await cachedGet(`${API_URL}/categories`, {}, staticCache);
    } catch (error) {
        console.error("Error fetching categories:", error);
        return [];
    }
};

/**
 * Get all super categories (static, long cache)
 */
export const fetchSuperCategories = async () => {
    try {
        return await cachedGet(`${API_URL}/super-categories`, {}, staticCache);
    } catch (error) {
        console.error("Error fetching super categories:", error);
        return [];
    }
};

/**
 * Get POIs by category (cache for 2 min since these are large)
 */
export const fetchPOIsByCategory = async (category, limit = 500) => {
    try {
        return await cachedGet(`${API_URL}/pois/by-category`, { category, limit }, cache, 2 * 60 * 1000);
    } catch (error) {
        console.error("Error fetching POIs by category:", error);
        return [];
    }
};

/**
 * Get POIs by super category (cache for 2 min since these are large)
 */
export const fetchPOIsBySuperCategory = async (superCategory, limit = 500) => {
    try {
        return await cachedGet(`${API_URL}/pois/by-super-category`, { super_category: superCategory, limit }, cache, 2 * 60 * 1000);
    } catch (error) {
        console.error("Error fetching POIs by super category:", error);
        return [];
    }
};

/**
 * Get all Delhi areas with centroids (static, long cache)
 */
export const fetchAreas = async () => {
    try {
        return await cachedGet(`${API_URL}/areas`, {}, staticCache);
    } catch (error) {
        console.error("Error fetching areas:", error);
        return [];
    }
};

/**
 * Get Delhi city bounding box (static, long cache)
 */
export const fetchDelhiBounds = async () => {
    try {
        return await cachedGet(`${API_URL}/delhi/bounds`, {}, staticCache);
    } catch (error) {
        console.error("Error fetching Delhi bounds:", error);
        return null;
    }
};

/**
 * Check if a point is within Delhi city boundary (short cache)
 */
export const checkPointInDelhi = async (lat, lon) => {
    try {
        const data = await cachedGet(`${API_URL}/delhi/contains`, { lat, lon }, cache, 60 * 1000);
        return data.is_inside;
    } catch (error) {
        console.error("Error checking point in Delhi:", error);
        return false;
    }
};

// ============================================
// LatLong External API Functions (with caching)
// ============================================

/**
 * Get autocomplete suggestions (short cache since user is typing)
 */
export const fetchAutocomplete = async (query, lat = null, lon = null, limit = 10) => {
    try {
        const params = { query, limit };
        if (lat !== null) params.lat = lat;
        if (lon !== null) params.lon = lon;
        return await cachedGet(`${API_URL}/external/autocomplete`, params, cache, 60 * 1000);
    } catch (error) {
        console.error("Error fetching autocomplete:", error);
        return { status: "error", data: [] };
    }
};

/**
 * Convert address to coordinates (cache for 10 min)
 */
export const fetchGeocode = async (address) => {
    try {
        return await cachedGet(`${API_URL}/external/geocode`, { address }, cache, 10 * 60 * 1000);
    } catch (error) {
        console.error("Error fetching geocode:", error);
        return null;
    }
};

/**
 * Convert coordinates to address (cache for 10 min)
 */
export const fetchReverseGeocode = async (lat, lon) => {
    try {
        // Round coordinates to reduce cache keys (4 decimal = ~11m precision)
        const roundedLat = Math.round(lat * 10000) / 10000;
        const roundedLon = Math.round(lon * 10000) / 10000;
        return await cachedGet(`${API_URL}/external/reverse`, { lat: roundedLat, lon: roundedLon }, cache, 10 * 60 * 1000);
    } catch (error) {
        console.error("Error fetching reverse geocode:", error);
        return null;
    }
};

/**
 * Validate if an address matches given coordinates
 */
export const fetchValidateAddress = async (address, lat, lon) => {
    try {
        return await cachedGet(`${API_URL}/external/validate`, { address, lat, lon }, cache, 10 * 60 * 1000);
    } catch (error) {
        console.error("Error validating address:", error);
        return null;
    }
};

/**
 * Get nearby landmarks (cache for 5 min)
 */
export const fetchLandmarks = async (lat, lon) => {
    try {
        // Round coordinates for better cache hits
        const roundedLat = Math.round(lat * 10000) / 10000;
        const roundedLon = Math.round(lon * 10000) / 10000;
        return await cachedGet(`${API_URL}/external/landmarks`, { lat: roundedLat, lon: roundedLon }, cache, 5 * 60 * 1000);
    } catch (error) {
        console.error("Error fetching landmarks:", error);
        return null;
    }
};

/**
 * Get points of interest from external API
 */
export const fetchExternalPOI = async (lat, lon, category = null) => {
    try {
        const params = { lat: Math.round(lat * 10000) / 10000, lon: Math.round(lon * 10000) / 10000 };
        if (category) params.category = category;
        return await cachedGet(`${API_URL}/external/poi`, params, cache, 5 * 60 * 1000);
    } catch (error) {
        console.error("Error fetching external POI:", error);
        return null;
    }
};

/**
 * Get isochrone (cache for 5 min)
 */
export const fetchIsochrone = async (lat, lon, distance = 1.0) => {
    try {
        // Round coordinates for cache
        const roundedLat = Math.round(lat * 10000) / 10000;
        const roundedLon = Math.round(lon * 10000) / 10000;
        return await cachedGet(`${API_URL}/external/isochrone`, { lat: roundedLat, lon: roundedLon, distance }, cache, 5 * 60 * 1000);
    } catch (error) {
        console.error("Error fetching isochrone:", error);
        return null;
    }
};

// ============================================
// Business Location Recommendation
// ============================================

/**
 * Get business location recommendations
 * @param {string} query - Natural language query like "I want to open a cafe"
 * @param {number} radiusKm - Analysis radius in km (default 1.0)
 * @param {boolean} deepResearch - Enable real-time web research (default false)
 * @returns {Promise<object>} Recommendations with top 3 areas
 */
export const getLocationRecommendations = async (query, radiusKm = 1.0, deepResearch = false) => {
    try {
        const response = await axios.post(`${API_URL}/recommend/location`, {
            query,
            radius_km: radiusKm,
            deep_research: deepResearch
        });
        return response.data;
    } catch (error) {
        console.error("Error getting location recommendations:", error);
        throw error;
    }
};

/**
 * Get list of valid super categories for recommendations
 */
export const getRecommendCategories = async () => {
    try {
        return await cachedGet(`${API_URL}/recommend/categories`, {}, staticCache);
    } catch (error) {
        console.error("Error fetching recommendation categories:", error);
        return { categories: [] };
    }
};

/**
 * Get GeoJSON polygons for area names (for highlighting recommended areas)
 * @param {string[]} names - Array of area names
 * @returns {Promise<object>} GeoJSON FeatureCollection
 */
export const getAreaGeometry = async (names) => {
    if (!names || names.length === 0) return { type: "FeatureCollection", features: [] };
    try {
        const namesStr = names.join(',');
        return await cachedGet(`${API_URL}/areas/geometry`, { names: namesStr }, cache, 5 * 60 * 1000);
    } catch (error) {
        console.error("Error fetching area geometry:", error);
        return { type: "FeatureCollection", features: [] };
    }
};

/**
 * Analyze what businesses to open in a specific area
 * @param {string} area - Area name like "Hauz Khas"
 * @param {boolean} deepResearch - Enable real-time web research (default false)
 * @returns {Promise<object>} Analysis with recommendations
 */
export const analyzeAreaOpportunities = async (area, deepResearch = false) => {
    try {
        const response = await axios.post(`${API_URL}/analyze/area`, { 
            area,
            deep_research: deepResearch
        });
        return response.data;
    } catch (error) {
        console.error("Error analyzing area:", error);
        throw error;
    }
};

// Export cache for debugging/monitoring
export const getCacheStats = () => ({
    general: { size: cache.size, maxSize: cache.maxSize },
    viewport: { size: viewportCache.size, maxSize: viewportCache.maxSize },
    static: { size: staticCache.size, maxSize: staticCache.maxSize }
});

export const clearAllCaches = () => {
    cache.clear();
    viewportCache.clear();
    staticCache.clear();
    console.log('[Cache] All caches cleared');
};

