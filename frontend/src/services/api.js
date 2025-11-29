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

export const fetchExternalPOI = async (lat, lon, category) => {
    try {
        const response = await axios.get(`${API_URL}/external/poi`, { params: { lat, lon, category } });
        return response.data;
    } catch (error) {
        console.error("Error fetching external POI:", error);
        return null;
    }
};

export const fetchIsochrone = async (lat, lon, time) => {
    try {
        const response = await axios.get(`${API_URL}/external/isochrone`, { params: { lat, lon, time } });
        return response.data;
    } catch (error) {
        console.error("Error fetching isochrone:", error);
        return null;
    }
};
