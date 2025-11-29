from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.services.analysis import AnalysisService
from app.services.ai_agent import AIAgentService
from app.services.latlong_client import LatLongClient
from app.core.db import get_db_cursor, execute_query
import json

agent = AIAgentService()
latlong_client = LatLongClient()
router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0", "db": "postgis"}

@router.get("/points", response_model=List[dict])
def get_points(category: Optional[str] = None, limit: int = 2000):
    """
    Get points of interest from delhi_points table.
    Only returns points within Delhi bounds and limited to prevent memory issues.
    """
    # Delhi bounding box (approximate)
    min_lat, max_lat = 28.4, 28.9
    min_lon, max_lon = 76.8, 77.4
    
    if category:
        query = """
            SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon 
            FROM delhi_points
            WHERE ST_Y(geom) BETWEEN %s AND %s
            AND ST_X(geom) BETWEEN %s AND %s
            AND category = %s
            LIMIT %s
        """
        params = (min_lat, max_lat, min_lon, max_lon, category, limit)
    else:
        query = """
            SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon 
            FROM delhi_points
            WHERE ST_Y(geom) BETWEEN %s AND %s
            AND ST_X(geom) BETWEEN %s AND %s
            LIMIT %s
        """
        params = (min_lat, max_lat, min_lon, max_lon, limit)
    
    results = execute_query(query, params)
    
    return [
        {"id": r[0], "name": r[1], "category": r[2], "lat": r[3], "lon": r[4]}
        for r in results
    ]


@router.get("/points/viewport", response_model=List[dict])
def get_points_viewport(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    limit: int = 100,
    buffer_frac: float = 0.05
):
    """
    Return POIs within the given viewport bounding box.
    - Expands the bbox by `buffer_frac` (fraction of bbox size) to preload nearby points for smooth panning.
    - Ranks POIs by an importance score derived from `area_scores` when available.
    - Falls back to returning points from `points_area` (which has area mapping) if present.

    Params: min_lat, min_lon, max_lat, max_lon, limit, buffer_frac
    """
    # expand bbox slightly to preload nearby POIs
    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon
    pad_lat = lat_span * buffer_frac
    pad_lon = lon_span * buffer_frac

    q_min_lat = min_lat - pad_lat
    q_max_lat = max_lat + pad_lat
    q_min_lon = min_lon - pad_lon
    q_max_lon = max_lon + pad_lon

    # Use points_area joined to area_scores to compute importance
    query = """
        SELECT p.id, p.name, p.category, ST_Y(p.geom) as lat, ST_X(p.geom) as lon,
               COALESCE(a.score_footfall, 0) as footfall,
               COALESCE(a.score_poi_synergy, 0) as poi_synergy,
               COALESCE(a.score_transit, 0) as transit,
               (COALESCE(a.score_footfall, 0)*0.5 + COALESCE(a.score_poi_synergy, 0)*0.3 + COALESCE(a.score_transit, 0)*0.2) as importance
        FROM points_area p
        LEFT JOIN area_scores a ON p.area = a.name
        WHERE ST_Y(p.geom) BETWEEN %s AND %s
          AND ST_X(p.geom) BETWEEN %s AND %s
        ORDER BY importance DESC
        LIMIT %s
    """
    params = (q_min_lat, q_max_lat, q_min_lon, q_max_lon, limit)

    try:
        results = execute_query(query, params)
    except Exception:
        # Fallback: if points_area/area_scores not available, query delhi_points directly
        fallback_q = """
            SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon
            FROM delhi_points
            WHERE ST_Y(geom) BETWEEN %s AND %s
              AND ST_X(geom) BETWEEN %s AND %s
            LIMIT %s
        """
        results = execute_query(fallback_q, (q_min_lat, q_max_lat, q_min_lon, q_max_lon, limit))

    return [
        {"id": r[0], "name": r[1], "category": r[2], "lat": r[3], "lon": r[4]}
        for r in results
    ]

@router.get("/areas", response_model=List[dict])
def get_areas():
    """
    Get all areas/districts from delhi_area table with centroids
    """
    query = """
        SELECT id, name, longitude, latitude 
        FROM area_with_centroid 
        ORDER BY name
    """
    results = execute_query(query)
    
    return [
        {"id": r[0], "name": r[1], "lon": r[2], "lat": r[3]}
        for r in results
    ]

@router.get("/areas/search")
def search_areas(q: str, limit: int = 10):
    """
    Search areas by name with fuzzy matching.
    Returns areas with centroids for map navigation.
    """
    # PostgreSQL ILIKE for case-insensitive search
    query = """
        SELECT id, name, longitude, latitude 
        FROM area_with_centroid 
        WHERE name ILIKE %s
        ORDER BY 
            CASE WHEN LOWER(name) = LOWER(%s) THEN 0
                 WHEN name ILIKE %s THEN 1
                 ELSE 2 END,
            name
        LIMIT %s
    """
    search_term = f"%{q}%"
    starts_with = f"{q}%"
    results = execute_query(query, (search_term, q, starts_with, limit))
    
    return [{
        "id": r[0],
        "name": r[1],
        "lon": r[2],
        "lat": r[3],
        "type": "area"
    } for r in results]

@router.get("/delhi/bounds")
def get_delhi_bounds():
    """
    Get Delhi city boundary bounding box from the database.
    Used for validating if coordinates are within Delhi.
    """
    query = """
        SELECT 
            ST_XMin(geom) as min_lon,
            ST_XMax(geom) as max_lon,
            ST_YMin(geom) as min_lat,
            ST_YMax(geom) as max_lat
        FROM delhi_city
        LIMIT 1
    """
    result = execute_query(query, fetch="one")
    
    if result:
        return {
            "min_lon": result[0],
            "max_lon": result[1],
            "min_lat": result[2],
            "max_lat": result[3]
        }
    return None

@router.get("/delhi/contains")
def check_point_in_delhi(lat: float, lon: float):
    """
    Check if a point is within the Delhi city boundary polygon.
    Uses actual geometry for precise validation.
    """
    query = """
        SELECT ST_Contains(geom, ST_SetSRID(ST_Point(%s, %s), 4326)) as is_inside
        FROM delhi_city
        LIMIT 1
    """
    result = execute_query(query, (lon, lat), fetch="one")
    
    return {"is_inside": bool(result[0]) if result else False}

@router.get("/pincodes", response_model=List[dict])
def get_pincodes():
    """
    Get all pincodes from delhi_pincode table
    """
    query = "SELECT id, name FROM delhi_pincode"
    results = execute_query(query)
    
    return [{"id": r[0], "pincode": r[1]} for r in results]

@router.post("/analyze/score")
def calculate_score(
    traffic: float,
    competition: float,
    demand: float,
    access: float,
    synergy: float
):
    score = AnalysisService.calculate_score(traffic, competition, demand, access, synergy)
    return {"score": score, "grade": "A" if score > 8 else "B" if score > 6 else "C"}

@router.post("/analyze/clusters")
def analyze_clusters(locations: List[List[float]]):
    """
    Input: List of [lat, lon]
    """
    result = AnalysisService.cluster_competitors(locations)
    return result

@router.post("/chat")
def chat(message: dict):
    """
    Input: {"message": "Show me competitors"}
    Output: {"text": "...", "actions": [...]}
    """
    user_text = message.get("message", "")
    response = agent.process_message(user_text)
    return response

@router.get("/delhi_boundary")
def get_delhi_boundary():
    """Get Delhi city boundary as GeoJSON."""
    try:
        query = "SELECT ST_AsGeoJSON(geom) as geometry, name FROM delhi_city LIMIT 1"
        results = execute_query(query)
        
        features = []
        for r in results:
            features.append({
                "type": "Feature",
                "geometry": json.loads(r[0]),
                "properties": {"name": r[1]}
            })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        print(f"Error fetching boundary: {e}")
        return {"type": "FeatureCollection", "features": []}

@router.get("/external/poi")
def get_external_poi(lat: float, lon: float, category: Optional[str] = None):
    """Get points of interest near a location from LatLong API."""
    return latlong_client.get_pois(lat, lon, category=category)

@router.get("/external/reverse")
def get_external_reverse(lat: float, lon: float):
    """Get address for coordinates from LatLong API."""
    return latlong_client.reverse_geocode(lat, lon)

@router.get("/external/isochrone")
def get_external_isochrone(lat: float, lon: float, distance: float = 1.0):
    """Get isochrone (reachable area) polygon from LatLong API."""
    return latlong_client.get_isochrone(lat, lon, distance_km=distance)

@router.get("/external/distance")
def get_external_distance(lat1: float, lon1: float, lat2: float, lon2: float):
    """Get distance between two points."""
    return latlong_client.get_distance(lat1, lon1, lat2, lon2)

@router.get("/external/autocomplete")
def get_external_autocomplete(query: str, lat: Optional[float] = None, lon: Optional[float] = None, limit: int = 10):
    """Get autocomplete suggestions for a search query from LatLong API."""
    return latlong_client.autocomplete(query, lat=lat, lon=lon, limit=limit)

@router.get("/external/geocode")
def get_external_geocode(address: str):
    """Convert address to coordinates using LatLong API."""
    return latlong_client.geocode(address)

@router.get("/external/validate")
def get_external_validate(address: str, lat: float, lon: float):
    """Validate if an address matches given coordinates using LatLong API."""
    return latlong_client.validate_address(address, lat, lon)

@router.get("/external/landmarks")
def get_external_landmarks(lat: float, lon: float):
    """Get nearby landmarks from LatLong API."""
    return latlong_client.get_landmarks(lat, lon)
