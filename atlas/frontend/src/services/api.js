import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

export const fetchPOIs = async (category) => {
    try {
        const response = await axios.get(`${API_URL}/pois`, { params: { category } });
        return response.data;
    } catch (error) {
        console.error("Error fetching POIs:", error);
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
