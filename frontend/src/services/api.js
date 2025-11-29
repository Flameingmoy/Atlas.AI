import axios from 'axios';

const API_URL = '/api';

export const fetchPoints = async (category) => {
    try {
        const response = await axios.get(`${API_URL}/points`, { params: { category } });
        return response.data;
    } catch (error) {
        console.error("Error fetching points:", error);
        return [];
    }
};

// Backward compatibility alias
export const fetchPOIs = fetchPoints;

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
        const response = await axios.get(`${API_URL}/delhi_boundary`);
        return response.data;
    } catch (error) {
        console.error("Error fetching boundary:", error);
        return null;
    }
};

// ============================================
// LatLong External API Functions
// ============================================

/**
 * Get autocomplete suggestions for a search query
 * @param {string} query - Search text
 * @param {number} lat - Optional latitude for location-biased results
 * @param {number} lon - Optional longitude for location-biased results
 * @param {number} limit - Maximum results (default 10)
 */
export const fetchAutocomplete = async (query, lat = null, lon = null, limit = 10) => {
    try {
        const params = { query, limit };
        if (lat !== null) params.lat = lat;
        if (lon !== null) params.lon = lon;
        const response = await axios.get(`${API_URL}/external/autocomplete`, { params });
        return response.data;
    } catch (error) {
        console.error("Error fetching autocomplete:", error);
        return { status: "error", data: [] };
    }
};

/**
 * Convert address to coordinates (geocoding)
 * @param {string} address - Full address string
 */
export const fetchGeocode = async (address) => {
    try {
        const response = await axios.get(`${API_URL}/external/geocode`, { params: { address } });
        return response.data;
    } catch (error) {
        console.error("Error fetching geocode:", error);
        return null;
    }
};

/**
 * Convert coordinates to address (reverse geocoding)
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 */
export const fetchReverseGeocode = async (lat, lon) => {
    try {
        const response = await axios.get(`${API_URL}/external/reverse`, { params: { lat, lon } });
        return response.data;
    } catch (error) {
        console.error("Error fetching reverse geocode:", error);
        return null;
    }
};

/**
 * Validate if an address matches given coordinates
 * @param {string} address - Address to validate
 * @param {number} lat - Expected latitude
 * @param {number} lon - Expected longitude
 */
export const fetchValidateAddress = async (address, lat, lon) => {
    try {
        const response = await axios.get(`${API_URL}/external/validate`, { params: { address, lat, lon } });
        return response.data;
    } catch (error) {
        console.error("Error validating address:", error);
        return null;
    }
};

/**
 * Get nearby landmarks
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 */
export const fetchLandmarks = async (lat, lon) => {
    try {
        const response = await axios.get(`${API_URL}/external/landmarks`, { params: { lat, lon } });
        return response.data;
    } catch (error) {
        console.error("Error fetching landmarks:", error);
        return null;
    }
};

/**
 * Get points of interest from external API
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @param {string} category - Optional category filter
 */
export const fetchExternalPOI = async (lat, lon, category = null) => {
    try {
        const params = { lat, lon };
        if (category) params.category = category;
        const response = await axios.get(`${API_URL}/external/poi`, { params });
        return response.data;
    } catch (error) {
        console.error("Error fetching external POI:", error);
        return null;
    }
};

/**
 * Get isochrone (reachable area polygon)
 * @param {number} lat - Center latitude
 * @param {number} lon - Center longitude
 * @param {number} distance - Distance in kilometers (default 1.0)
 */
export const fetchIsochrone = async (lat, lon, distance = 1.0) => {
    try {
        const response = await axios.get(`${API_URL}/external/isochrone`, { params: { lat, lon, distance } });
        return response.data;
    } catch (error) {
        console.error("Error fetching isochrone:", error);
        return null;
    }
};
