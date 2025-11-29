import os
import requests
from typing import Dict, Any, Optional, List

class LatLongClient:
    """
    Client for LatLong.ai API Hub services.
    API Documentation: https://apihub.latlong.ai
    """
    
    def __init__(self):
        self.token = os.getenv("LATLONG_TOKEN")
        self.base_url = "https://apihub.latlong.ai/v4"
        if not self.token:
            print("Warning: LATLONG_TOKEN not set in environment variables")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with X-Authorization-Token for LatLong API."""
        return {
            "X-Authorization-Token": self.token
        }

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a GET request to the LatLong API."""
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                headers=self._get_headers(),
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e)}

    def autocomplete(self, query: str, lat: Optional[float] = None, lon: Optional[float] = None, 
                     limit: int = 10, language: str = "en") -> Dict[str, Any]:
        """
        Get autocomplete suggestions for a search query.
        
        Args:
            query: Search text (e.g., "delhi", "connaught place")
            lat: Optional latitude for location-biased results
            lon: Optional longitude for location-biased results
            limit: Maximum number of results (default 10)
            language: Response language (default "en")
        
        Returns:
            List of place suggestions with geoid and name
        """
        params = {
            "query": query,
            "limit": limit,
            "language": language
        }
        if lat is not None:
            params["lat"] = lat
        if lon is not None:
            params["lon"] = lon
            
        return self._make_request("autocomplete.json", params)

    def geocode(self, address: str, accuracy_level: bool = True) -> Dict[str, Any]:
        """
        Convert an address to latitude/longitude coordinates.
        
        Args:
            address: Full address string
            accuracy_level: Whether to include accuracy info (default True)
        
        Returns:
            Coordinates and accuracy level for the address
        """
        params = {
            "address": address,
            "accuracy_level": str(accuracy_level).lower()
        }
        return self._make_request("geocode.json", params)

    def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Convert coordinates to a human-readable address.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Address, pincode, landmark, and building name
        """
        params = {
            "latitude": lat,
            "longitude": lon
        }
        return self._make_request("reverse_geocode.json", params)

    def validate_address(self, address: str, lat: float, lon: float) -> Dict[str, Any]:
        """
        Validate if an address matches given coordinates.
        
        Args:
            address: Address to validate
            lat: Expected latitude
            lon: Expected longitude
        
        Returns:
            Validation results showing which components match (Colony, Locality, City, etc.)
        """
        params = {
            "address": address,
            "latitude": lat,
            "longitude": lon
        }
        return self._make_request("geovalidation.json", params)

    def get_isochrone(self, lat: float, lon: float, distance_km: float = 1.0) -> Dict[str, Any]:
        """
        Get isochrone polygon showing reachable area from a point.
        
        Args:
            lat: Center latitude
            lon: Center longitude
            distance_km: Distance limit in kilometers (default 1.0)
        
        Returns:
            GeoJSON Feature with polygon geometry
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "distance_limit": distance_km
        }
        return self._make_request("isochrone.json", params)

    def get_landmarks(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get nearby landmarks for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            List of nearby landmarks with names and coordinates
        """
        params = {
            "lat": lat,
            "lon": lon
        }
        return self._make_request("landmarks.json", params)

    def get_pois(self, lat: float, lon: float, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get points of interest near a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            category: Comma-separated categories (e.g., "MORTH,Pin Code")
        
        Returns:
            List of POIs with category and name
        """
        params = {
            "latitude": lat,
            "longitude": lon
        }
        if category:
            params["category"] = category
            
        return self._make_request("point_of_interest.json", params)

    # Convenience method for backward compatibility
    def get_distance(self, origin_lat: float, origin_lon: float, 
                     dest_lat: float, dest_lon: float) -> Dict[str, Any]:
        """
        Get distance between two points using geovalidation API.
        Note: This is a workaround using geovalidation to get driving distance.
        
        Args:
            origin_lat, origin_lon: Origin coordinates
            dest_lat, dest_lon: Destination coordinates
        
        Returns:
            Aerial and driving distance between points
        """
        # Use geovalidation with a dummy address to get distance info
        # This is limited - for full routing, a dedicated routing API would be needed
        result = self.validate_address(
            address="Distance calculation point",
            lat=dest_lat,
            lon=dest_lon
        )
        
        if result.get("status") == "success" and "data" in result:
            distance_data = result["data"].get("distance", {})
            return {
                "status": "success",
                "aerial_distance": distance_data.get("aerial", "N/A"),
                "driving_distance": distance_data.get("driving", "N/A")
            }
        
        # Fallback: Calculate aerial distance manually
        import math
        R = 6371  # Earth's radius in km
        lat1, lon1 = math.radians(origin_lat), math.radians(origin_lon)
        lat2, lon2 = math.radians(dest_lat), math.radians(dest_lon)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = R * c
        
        return {
            "status": "calculated",
            "aerial_distance": f"{distance_km:.2f} km",
            "driving_distance": "N/A"
        }
